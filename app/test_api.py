from fastapi import FastAPI, HTTPException
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
from fastapi import Path, Body
from app.services.firebase_service import init_firebase

# 환경변수 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# 환경변수에서 가져오기
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION", "ap-northeast-2")

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


KST = timezone(timedelta(hours=9))

# ✅ Firebase 초기화
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DB_URL
        })

# ✅ Firebase 먼저 초기화
init_firebase()

# ✅ Firestore 인스턴스
db = firestore.client()
collection_doctors = db.collection("doctors")
collection_admins = db.collection("admins")



# ✅ FastAPI 인스턴스
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "테스트 성공"}

# 병원 목록 가져오기
@app.get("/test/hospitals")
def get_hospitals():
    response = table_hospitals.scan()
    return {"hospitals": response.get("Items", [])}

# 의사 로그인
@app.post("/test/login/doctor")
def login_doctor(payload: dict):
    public_health_center = payload.get("public_health_center")
    department = payload.get("department")
    password = payload.get("password")

    if not (public_health_center and department and password):
        raise HTTPException(status_code=400, detail="입력값이 부족합니다.")

    # 1. 병원 ID 가져오기 (name은 예약어이므로 대체)
    response = table_hospitals.scan(
        FilterExpression=Attr("name").eq(public_health_center)
    )
    items = response.get("Items", [])
    if not items:
        raise HTTPException(status_code=404, detail="해당 보건소를 찾을 수 없습니다.")
    
    hospital_id = items[0].get("hospital_id")
    if hospital_id is None:
        raise HTTPException(status_code=500, detail="hospital_id 누락")
    #  Decimal → int 변환
    hospital_id = int(hospital_id)

    # 2. 의사 조회
    doctors = collection_doctors \
        .where("hospital_id", "==", hospital_id) \
        .where("department", "==", department) \
        .stream()

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


# 관리자 로그인 요청 모델
class AdminLoginRequest(BaseModel):
    public_health_center: str
    password: str

# 관리자 로그인 API
@app.post("/test/login/admin")
def login_admin(data: dict):
    public_health_center = data.get("public_health_center")
    password = data.get("password")

    # 병원 이름으로 hospital_id 찾기 (DynamoDB 기준)
    response = table_hospitals.scan(
        FilterExpression=Attr("name").eq(public_health_center)
    )
    items = response.get("Items", [])
    if not items:
        return {"error": "보건소 정보를 찾을 수 없습니다."}
    
    hospital_id = str(items[0].get("hospital_id"))  # ← 문자열로 변환

    # 🔐 Firestore에서 문서 ID 직접 접근
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
#의사 등록
@app.post("/test/register/doctor")
def register_doctor(data: dict):
    try:
        hospital_name = data.get("hospital_name")
        response = table_hospitals.scan(
            FilterExpression=Attr("name").eq(hospital_name)
        )
        items = response.get("Items", [])
        if not items:
            return {"error": "보건소 정보가 없습니다."}

        # ✅ Decimal로 변환 (Firestore는 Decimal 안받음 → int로 바꿔야 함)
        hospital_id = int(items[0].get("hospital_id"))

        license_number = str(uuid4().int)[:6]
        default_profile_url = "https://cdn-icons-png.flaticon.com/512/3870/3870822.png"

        collection_doctors.document(license_number).set({
            "hospital_id": hospital_id,  # 🔁 Decimal → int
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

#의사 목록 조회 
@app.get("/test/doctors")
def list_doctors():
    try:
        doctors = collection_doctors.stream()
        result = []
        for doc in doctors:
            data = doc.to_dict()
            data["license_number"] = doc.id  # 문서 ID 추가 (삭제용)
            result.append(data)
        return {"doctors": result}
    except Exception as e:
        return {"error": str(e)}
    
from fastapi import HTTPException, Path

#의사 삭제
@app.delete("/test/delete/doctor/{license_number}")
def delete_doctor(license_number: str = Path(..., description="의사 면허번호(문서 ID)")):
    try:
        doc_ref = collection_doctors.document(license_number)
        if not doc_ref.get().exists:
            raise HTTPException(status_code=404, detail="해당 의사를 찾을 수 없습니다.")
        
        doc_ref.delete()
        return {"message": "의사 삭제 완료", "license_number": license_number}
    except Exception as e:
        return {"error": str(e)}

#의사 수정 
@app.put("/test/update/doctor/{license_number}")
def update_doctor(
    license_number: str = Path(..., description="의사 면허번호(문서 ID)"),
    data: dict = Body(...)
):
    try:
        doc_ref = collection_doctors.document(license_number)
        if not doc_ref.get().exists:
            raise HTTPException(status_code=404, detail="의사를 찾을 수 없습니다.")
        
        # 허용 필드만 업데이트
        update_fields = {
            key: value for key, value in data.items()
            if key in [
                "name", "email", "department", "contact", 
                "gender", "bio", "availability", "profile_url"
            ]
        }

        if not update_fields:
            raise HTTPException(status_code=400, detail="수정할 필드가 없습니다.")

        doc_ref.update(update_fields)
        return {"message": "의사 정보 수정 완료", "updated_fields": update_fields}
    except Exception as e:
        return {"error": str(e)}
    
#질병 코드 조회
@app.get("/test/diseases")
def get_disease_codes():
    try:
        response = table_diseases.scan()
        items = response.get("Items", [])
        return {"diseases": items}
    except Exception as e:
        return {"error": str(e)}
    

# 1. 통화 방 생성 (Create)
@app.post("/test/video-call/create")
def create_video_call(payload: dict):
    doctor_id = payload.get("doctor_id")
    patient_id = payload.get("patient_id")

    if not doctor_id or not patient_id:
        raise HTTPException(status_code=400, detail="doctor_id와 patient_id는 필수입니다.")

    KST = timezone(timedelta(hours=9))
    timestamp = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
    safe_patient_id = patient_id.split("@")[0]
    room_id = f"doctor_{doctor_id}_patient_{safe_patient_id}_{timestamp}"

    # RealtimeDB 초기값
    realtime_db.reference(f"calls/{room_id}").set({
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "is_accepted": False,
        "status": "waiting",
        "created_at": timestamp
    })

    # Firestore 초기값
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
@app.post("/test/video-call/start")
def start_video_call(payload: dict):
    room_id = payload.get("room_id")

    if not room_id:
        raise HTTPException(status_code=400, detail="room_id는 필수입니다.")

    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    # Firestore 업데이트
    firestore.client().collection("calls").document(room_id).update({
        "started_at": now,
        "is_accepted": True
    })

    # RealtimeDB 상태 변경
    realtime_db.reference(f"calls/{room_id}").update({
        "status": "accepted"
    })

    return {"message": "통화 시작 처리 완료", "started_at": now}

# 통화 종료 (End)
@app.post("/test/video-call/end")
def end_video_call(payload: dict):
    room_id = payload.get("room_id")

    if not room_id:
        raise HTTPException(status_code=400, detail="room_id는 필수입니다.")

    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    # Firestore 종료시간 업데이트
    firestore.client().collection("calls").document(room_id).update({
        "ended_at": now
    })

    # RealtimeDB 상태 변경
    realtime_db.reference(f"calls/{room_id}").update({
        "status": "ended"
    })

    return {"message": "통화 종료 처리 완료", "ended_at": now}


# 실시간 텍스트 저장 (Text)
@app.post("/test/video-call/text")
def save_video_text(payload: dict):
    room_id = payload.get("room_id")
    role = payload.get("role")  # "doctor" 또는 "patient"
    text = payload.get("text")

    if not room_id or role not in ("doctor", "patient") or not text:
        raise HTTPException(status_code=400, detail="room_id, role, text는 필수입니다.")

    doc_ref = firestore.client().collection("calls").document(room_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="해당 통화 문서를 찾을 수 없습니다.")

    # 텍스트 배열 업데이트
    doc_ref.update({
        f"{role}_text": firestore.ArrayUnion([text])
    })

    return {"message": f"{role}의 텍스트가 저장되었습니다."}

# 환자리스트 호출 
@app.get("/test/patients")
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
@app.get("/test/care-requests")
def get_all_care_requests():
    try:
        table_care_requests = dynamodb.Table("care_requests")  # 🔹 테이블 객체 선언
        response = table_care_requests.scan()
        items = response.get("Items", [])
        return {"care_requests": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# 진료 대기(진료신청) 인원만 보이도록 
@app.get("/test/care-requests/waiting")
def get_waiting_care_requests():
    try:
        # 1. 진료 요청 중 대기 상태만 조회
        table_care_requests = dynamodb.Table("care_requests")
        response = table_care_requests.scan(
            FilterExpression=Attr("is_solved").eq(False)
        )
        care_requests = response.get("Items", [])

        result = []
        for request in care_requests:
            patient_id = request.get("patient_id")
            if not patient_id:
                continue

            # 2. Firestore에서 환자 정보 가져오기
            patient_doc = db.collection("patients").document(patient_id).get()
            if not patient_doc.exists:
                continue

            patient_data = patient_doc.to_dict()

            # 3. 병합 데이터 구성
            combined = {
                "request_id": request.get("request_id"),
                "name": patient_data.get("name"),
                "sign_language_needed": request.get("sign_language_needed", False),
                "birth": patient_data.get("birth", None),
                "department": request.get("department"),
                "book_date": request.get("book_date"),
                "book_hour": request.get("book_hour"),
                "symptom_part": request.get("symptom_part", []),
                "symptom_type": request.get("symptom_type", [])
            }
            result.append(combined)

        return {"waiting_list": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))