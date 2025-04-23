from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# 템플릿 경로 지정
templates = Jinja2Templates(directory="app/api/templates")
router = APIRouter(prefix="/doctor", tags=["Doctor"])

# 진료 대기 목록 페이지
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from firebase_admin import firestore

router = APIRouter(prefix="/doctor", tags=["Doctor"])
templates = Jinja2Templates(directory="app/api/templates")
# db = firestore.client()

@router.get("/video-call/{consultation_id}", response_class=HTMLResponse)
async def video_call_page(request: Request, consultation_id: str):
    # 하드코딩된 진료 데이터
    consultation = {
        "consultation_id": consultation_id,
        "patient_id": "p001",
        "doctor_id": "d001",
        "previous_date": "2024-01-10",
        "previous_disease_code": "DIS001"
    }

    # 하드코딩된 환자 정보
    patient = {
        "name": "홍길동",
        "birth": "040324",
        "gender": "남",
        "symptom_area": "목",
        "main_symptom": "기침"
    }

    return templates.TemplateResponse("video_call.html", {
        "request": request,
        "consultation_id": consultation_id,
        "consultation": consultation,
        "patient": patient,
        "active_tab": "video"
    })