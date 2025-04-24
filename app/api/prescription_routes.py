from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import uuid

router = APIRouter()

# HTML Form 기반 기존 라우터 (유지)
@router.post("/prescription/submit")
async def submit_prescription(
    request: Request,
    patient_id: str = Form(...),
    doctor_id: str = Form(...),
    disease_code: str = Form(...),
    medication_code: str = Form(...),
    days: int = Form(...),
    memo: str = Form("")
):
    prescription_id = str(uuid.uuid4())
    # TODO: DB에 저장 처리
    return RedirectResponse(url="/doctor/consultation", status_code=302)

# ✅ JSON 기반 API 버전 (Postman 테스트용)
class PrescriptionRequest(BaseModel):
    patient_id: str
    doctor_id: str
    disease_code: str
    medication_code: str
    days: int
    memo: str = ""

@router.post("/api/prescription/submit")
async def submit_prescription_api(data: PrescriptionRequest):
    prescription_id = str(uuid.uuid4())
    # TODO: DB 저장 처리 (DynamoDB or 기타)
    return {
        "status_code": 200,
        "message": "처방전 저장 완료",
        "prescription_id": prescription_id
    }