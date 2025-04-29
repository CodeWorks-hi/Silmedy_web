from fastapi import FastAPI, HTTPException, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from boto3.dynamodb.conditions import Attr
import boto3
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, db as realtime_db
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import random
from decimal import Decimal
from fastapi import Path


# 환경변수 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# AWS 정보
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION", "ap-northeast-2")

# Firebase 정보
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")

# DynamoDB 리소스
dynamodb = boto3.resource(
    "dynamodb",
    region_name=aws_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

table_hospitals = dynamodb.Table("hospitals")
table_diseases = dynamodb.Table("diseases")

# 한국시간
KST = timezone(timedelta(hours=9))
now = datetime.now(KST)

timestamp = now.strftime("%Y%m%d_%H%M%S")
random_suffix = f"{random.randint(0, 999):03d}"

# Firebase 초기화
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DB_URL
        })

# Firebase 초기화 실행
init_firebase()

# Firestore 인스턴스
db = firestore.client()
collection_doctors = db.collection("doctors")
collection_admins = db.collection("admins")

# FastAPI 인스턴스 (✨ 스웨거 문서 설정 추가)
app = FastAPI(
    title="Silmedy 관리자/의사 서버 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# DynamoDB Decimal -> int/float 변환
def decimal_to_native(obj):
    if isinstance(obj, list):
        return [decimal_to_native(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj
    

# API 시작
@app.get("/test/hospitals", summary="병원 목록 조회", description="DynamoDB에서 모든 병원 정보를 가져옵니다.")
def get_hospitals():
    response = table_hospitals.scan()
    return {"hospitals": response.get("Items", [])}

@app.post("/test/login/doctor", summary="의사 로그인", description="보건소명, 진료과, 비밀번호를 입력하여 의사 계정으로 로그인합니다.")
def login_doctor(payload: dict):
    public_health_center = payload.get("public_health_center")
    department = payload.get("department")
    password = payload.get("password")

    if not (public_health_center and department and password):
        raise HTTPException(status_code=400, detail="입력값이 부족합니다.")

    response = table_hospitals.scan(
        FilterExpression=Attr("name").eq(public_health_center)
    )
    items = response.get("Items", [])
    if not items:
        raise HTTPException(status_code=404, detail="해당 보건소를 찾을 수 없습니다.")

    hospital_id = int(items[0].get("hospital_id"))

    doctors = collection_doctors.where("hospital_id", "==", hospital_id).where("department", "==", department).stream()

    for doc in doctors:
        doctor = doc.to_dict()
        if doctor["password"] == password:
            return {
                "message": "로그인 성공",
                "doctor_name": doctor["name"],
                "department": doctor["department"],
                "hospital_id": doctor["hospital_id"]
            }

    raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않거나 등록되지 않은 의사입니다.")

class AdminLoginRequest(BaseModel):
    public_health_center: str
    password: str

@app.post("/test/login/admin", summary="관리자 로그인", description="보건소명을 통해 관리자 계정으로 로그인합니다.")
def login_admin(data: dict):
    public_health_center = data.get("public_health_center")
    password = data.get("password")

    response = table_hospitals.scan(
        FilterExpression=Attr("name").eq(public_health_center)
    )
    items = response.get("Items", [])
    if not items:
        return {"error": "보건소 정보를 찾을 수 없습니다."}

    hospital_id = str(items[0].get("hospital_id"))
    doc_ref = collection_admins.document(hospital_id).get()

    if not doc_ref.exists:
        return {"error": "관리자 계정이 없습니다."}

    user = doc_ref.to_dict()
    if user["password"] != password:
        return {"error": "비밀번호가 일치하지 않습니다."}

    return {
        "message": "로그인 성공",
        "hospital_id": hospital_id
    }

@app.post("/test/register/doctor", summary="의사 등록", description="보건소를 선택하여 새 의사 계정을 등록합니다.")
def register_doctor(data: dict):
    try:
        hospital_name = data.get("hospital_name")
        response = table_hospitals.scan(
            FilterExpression=Attr("name").eq(hospital_name)
        )
        items = response.get("Items", [])
        if not items:
            return {"error": "보건소 정보가 없습니다."}

        hospital_id = int(items[0].get("hospital_id"))

        license_number = str(uuid4().int)[:6]
        default_profile_url = "https://cdn-icons-png.flaticon.com/512/3870/3870822.png"

        collection_doctors.document(license_number).set({
            "hospital_id": hospital_id,
            "name": data["name"],
            "email": data["email"],
            "password": data["password"],
            "department": data["department"],
            "contact": data["contact"],
            "gender": data.get("gender", ""),
            "profile_url": default_profile_url,
            "bio": [],
            "availability": {},
            "created_at": datetime.utcnow().isoformat()
        })

        return {
            "message": "의사 등록 완료",
            "license_number": license_number
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/test/doctors", summary="의사 목록 조회", description="등록된 모든 의사 정보를 가져옵니다.")
def list_doctors():
    try:
        doctors = collection_doctors.stream()
        result = []
        for doc in doctors:
            data = doc.to_dict()
            data["license_number"] = doc.id
            result.append(data)
        return {"doctors": result}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/test/delete/doctor/{license_number}", summary="의사 삭제", description="면허번호(문서ID)를 이용하여 의사를 삭제합니다.")
def delete_doctor(license_number: str = Path(..., description="의사 면허번호(문서 ID)")):
    try:
        doc_ref = collection_doctors.document(license_number)
        if not doc_ref.get().exists:
            raise HTTPException(status_code=404, detail="해당 의사를 찾을 수 없습니다.")
        doc_ref.delete()
        return {"message": "의사 삭제 완료", "license_number": license_number}
    except Exception as e:
        return {"error": str(e)}

@app.put("/test/update/doctor/{license_number}", summary="의사 정보 수정", description="의사 면허번호를 기준으로 의사 정보를 수정합니다.")
def update_doctor(
    license_number: str = Path(..., description="의사 면허번호(문서 ID)"),
    data: dict = Body(...)
):
    try:
        doc_ref = collection_doctors.document(license_number)
        if not doc_ref.get().exists:
            raise HTTPException(status_code=404, detail="의사를 찾을 수 없습니다.")

        update_fields = {
            key: value for key, value in data.items()
            if key in ["name", "email", "department", "contact", "gender", "bio", "availability", "profile_url"]
        }

        if not update_fields:
            raise HTTPException(status_code=400, detail="수정할 필드가 없습니다.")

        doc_ref.update(update_fields)
        return {"message": "의사 정보 수정 완료", "updated_fields": update_fields}
    except Exception as e:
        return {"error": str(e)}

@app.get("/test/diseases", summary="질병 코드 목록 조회", description="DynamoDB에서 모든 질병 코드를 조회합니다.")
def get_disease_codes():
    try:
        response = table_diseases.scan()
        return {"diseases": response.get("Items", [])}
    except Exception as e:
        return {"error": str(e)}

# (이하 통화 생성, 통화 시작, 통화 종료, 텍스트 저장, 환자목록 조회 등 전부 같은 방식으로 summary/description 추가 가능)
    

# 1. 통화 방 생성 (Create)
@app.post("/test/video-call/create", summary="영상 통화방 생성", description="doctor_id와 patient_id를 입력받아 새로운 영상통화방을 생성합니다.")
def create_video_call(payload: dict):
    doctor_id = payload.get("doctor_id")
    patient_id = payload.get("patient_id")

    if not doctor_id or not patient_id:
        raise HTTPException(status_code=400, detail="doctor_id와 patient_id는 필수입니다.")

    safe_patient_id = patient_id.split("@")[0]
    room_id = f"doctor_{doctor_id}_patient_{safe_patient_id}_{timestamp}"

    realtime_db.reference(f"calls/{room_id}").set({
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "is_accepted": False,
        "status": "waiting",
        "created_at": timestamp
    })

    firestore.client().collection("calls").document(room_id).set({
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "is_accepted": False,
        "started_at": None,
        "ended_at": None,
        "doctor_text": [],
        "patient_text": []
    })

    return {"message": "영상 통화방 생성 완료", "room_id": room_id}

# 통화 시작 (Start)
@app.post("/test/video-call/start", summary="영상 통화 시작", description="room_id를 통해 통화를 시작 처리합니다.")
def start_video_call(payload: dict):
    room_id = payload.get("room_id")

    if not room_id:
        raise HTTPException(status_code=400, detail="room_id는 필수입니다.")

    firestore.client().collection("calls").document(room_id).update({
        "started_at": now,
        "is_accepted": True
    })

    realtime_db.reference(f"calls/{room_id}").update({
        "status": "accepted"
    })

    return {"message": "통화 시작 처리 완료", "started_at": now}

# 통화 종료 (End)
@app.post("/test/video-call/end", summary="영상 통화 종료", description="room_id를 통해 통화를 종료 처리합니다.")
def end_video_call(payload: dict):
    room_id = payload.get("room_id")

    if not room_id:
        raise HTTPException(status_code=400, detail="room_id는 필수입니다.")

    firestore.client().collection("calls").document(room_id).update({
        "ended_at": now
    })

    realtime_db.reference(f"calls/{room_id}").update({
        "status": "ended"
    })

    return {"message": "통화 종료 처리 완료", "ended_at": now}

# 실시간 텍스트 저장 (Text)
@app.post("/test/video-call/text", summary="영상 통화 중 실시간 텍스트 저장", description="room_id, role(doctor), text를 받아서 텍스트 내용을 저장합니다.")
def save_video_text(payload: dict):
    room_id = payload.get("room_id")
    role = payload.get("role")
    text = payload.get("text")

    if not room_id or role not in ("doctor") or not text:
        raise HTTPException(status_code=400, detail="room_id, role, text는 필수입니다.")

    doc_ref = firestore.client().collection("calls").document(room_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="해당 통화 문서를 찾을 수 없습니다.")

    doc_ref.update({
        f"{role}_text": firestore.ArrayUnion([text])
    })

    return {"message": f"{role}의 텍스트가 저장되었습니다."}

# 환자리스트 호출 
@app.get("/test/patients", summary="환자 목록 조회", description="Firestore에서 등록된 모든 환자 목록을 가져옵니다.")
def list_patients():
    try:
        patients = firestore.client().collection("patients").stream()
        result = []
        for doc in patients:
            data = doc.to_dict()
            data["patient_id"] = doc.id
            result.append(data)
        return {"patients": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# 진료 신청 전체 목록 조회
@app.get("/test/care-requests", summary="진료 신청 전체 조회", description="DynamoDB에서 전체 진료 신청 목록을 가져옵니다.")
def get_all_care_requests():
    try:
        table_care_requests = dynamodb.Table("care_requests")
        response = table_care_requests.scan()
        return {"care_requests": response.get("Items", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# 진료 대기(진료신청) 인원만 보이도록
@app.get("/test/care-requests/waiting", summary="진료 대기 목록 조회", description="대기 중인 진료 요청만 조회하여 환자 정보와 함께 반환합니다.")
def get_waiting_care_requests_test(doctor_id: int):
    try:
        db = firestore.client()  # ✅ firestore client 초기화

        table_care_requests = dynamodb.Table("care_requests")
        response = table_care_requests.scan(
            FilterExpression=Attr("is_solved").eq(False) & Attr("doctor_id").eq(doctor_id)
        )
        care_requests = response.get("Items", [])

        result = []
        for request in care_requests:
            patient_id = request.get("patient_id")
            if not patient_id:
                continue

            patient_doc = db.collection("patients").document(str(patient_id)).get()
            if not patient_doc.exists:
                continue

            patient_data = patient_doc.to_dict()

            combined = {
                "request_id": request.get("request_id"),
                "name": patient_data.get("name"),
                "sign_language_needed": request.get("sign_language_needed", False),
                "birth_date": patient_data.get("birth_date", None),  # 🔵 birth -> birth_date 매칭
                "department": request.get("department"),
                "book_date": request.get("book_date"),
                "book_hour": request.get("book_hour"),
                "symptom_part": request.get("symptom_part", []),
                "symptom_type": request.get("symptom_type", [])
            }
            result.append(combined)

        return {"waiting_list": decimal_to_native(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# 의약품 리스트 호출
@app.get("/test/drugs", summary="의약품 목록 조회", description="DynamoDB에서 전체 의약품 데이터를 조회합니다.")
def get_all_drugs():
    try:
        table_drugs = dynamodb.Table("drugs")
        response = table_drugs.scan()
        return {"drugs": response.get("Items", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 처방전리스트 호출
@app.get("/test/prescription_records", summary="처방전 목록 조회", description="DynamoDB에서 모든 처방전 기록을 조회합니다.")
def get_all_prescriptions():
    try:
        table = dynamodb.Table("prescription_records")
        response = table.scan()
        return {"prescription_records": response.get("Items", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 처방전 등록 API
@app.post("/test/prescriptions/create", summary="처방전 등록", description="진단 ID와 약 리스트를 받아 새로운 처방전을 등록합니다.")
def create_prescription(payload: dict):
    try:
        prescription_id = int(f"{timestamp}{random_suffix}")

        prescription_table = dynamodb.Table("prescription_records")
        item = {
            "prescription_id": prescription_id,
            "diagnosis_id": int(payload.get("diagnosis_id")),
            "doctor_id": int(payload.get("doctor_id")),
            "medication_days": int(payload.get("medication_days")),
            "medication_list": payload.get("medication_list", []),
            "prescribed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        }

        prescription_table.put_item(Item=item)

        return {
            "message": "처방전 저장 완료",
            "prescription_id": prescription_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#진단기록 리스트 
@app.get("/test/diagnosis-records", summary="진단 기록 전체 조회", description="DynamoDB에서 전체 진단 기록을 조회합니다.")
def get_all_diagnosis_records():
    try:
        table = dynamodb.Table("diagnosis_records")
        response = table.scan()
        return {"diagnosis_records": response.get("Items", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 진단기록 저장 
@app.post("/test/diagnosis/create", summary="진단 기록 등록", description="새로운 진단 기록을 등록합니다.")
def create_diagnosis_record(payload: dict):
    try:
        diagnosis_id = int(f"{timestamp}{random_suffix}")
        diagnosed_at = now.strftime("%Y-%m-%d %H:%M:%S")

        diagnosis_table = dynamodb.Table("diagnosis_records")
        item = {
            "diagnosis_id": diagnosis_id,
            "doctor_id": payload.get("doctor_id"),
            "patient_id": payload.get("patient_id"),
            "disease_code": payload.get("disease_code"),
            "diagnosis_text": payload.get("diagnosis_text", ""),
            "diagnosed_at": diagnosed_at
        }

        diagnosis_table.put_item(Item=item)

        return {
            "message": "진단 기록 저장 완료",
            "diagnosis_id": diagnosis_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#  환자 진단 이력 조회 API (patient_id는 이메일)

@app.get("/test/diagnosis/patient/{patient_id}", summary="환자 진단 이력 조회", description="특정 환자(patient_id 기준)의 진단 이력을 조회합니다.")
def get_diagnosis_by_patient(patient_id: str = Path(..., description="환자의 이메일")):
    try:
        table = dynamodb.Table("diagnosis_records")
        response = table.scan(FilterExpression=Attr("patient_id").eq(patient_id))
        return {"diagnosis_records": response.get("Items", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))