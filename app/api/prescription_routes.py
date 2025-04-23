from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
import boto3
import uuid

router = APIRouter(prefix="/prescription", tags=["Prescription"])

# DynamoDB 설정 (리전은 필요에 따라 변경)
# dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-2")
# table = dynamodb.Table("prescriptions")

@router.post("/submit")
async def submit_prescription(
    request: Request,
    patient_id: str = Form(...),
    doctor_id: str = Form(...),
    memo: str = Form(""),
    disease_code: str = Form(...),
    medication_code: str = Form(...),
    days: int = Form(...)
):
    prescription_id = str(uuid.uuid4())
    item = {
        "prescription_id": prescription_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "memo": memo,
        "disease_code": disease_code,
        "medication_code": medication_code,
        "days": days,
        "status": "submitted"
    }
    print("처방전 데이터 (가상 저장):", item)
    # table.put_item(Item=item)

    return RedirectResponse(url="/doctor/consultation", status_code=302)
