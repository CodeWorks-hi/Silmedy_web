from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from boto3.dynamodb.conditions import Attr
import boto3
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
from fastapi import Path, Body

# ✅ 환경변수 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ✅ AWS 자격증명
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION", "ap-northeast-2")

# ✅ DynamoDB 리소스
dynamodb = boto3.resource(
    "dynamodb",
    region_name=aws_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

table_hospitals = dynamodb.Table("hospitals")
table_diseases = dynamodb.Table("diseases")

# ✅ Firebase 초기화
if not firebase_admin._apps:
    cred = credentials.Certificate("secrets/silmedy-23a1b-firebase-adminsdk-fbsvc-1e8c6b596b.json")
    firebase_admin.initialize_app(cred)

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

# ✅ 병원 목록 가져오기
@app.get("/test/hospitals")
def get_hospitals():
    response = table_hospitals.scan()
    return {"hospitals": response.get("Items", [])}

# ✅ 의사 로그인
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
    # 🔁 Decimal → int 변환
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


# 🔐 관리자 로그인 요청 모델
class AdminLoginRequest(BaseModel):
    public_health_center: str
    password: str

# ✅ 관리자 로그인 API
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
    
@app.get("/test/diseases")
def get_disease_codes():
    try:
        response = table_diseases.scan()
        items = response.get("Items", [])
        return {"diseases": items}
    except Exception as e:
        return {"error": str(e)}