from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# from firebase_admin import firestore  # 추후 연동 시 사용

# 라우터 및 템플릿 설정
router = APIRouter(prefix="/doctor", tags=["Doctor"])
templates = Jinja2Templates(directory="app/api/templates")
# db = firestore.client()  # 추후 Firebase 연동 시 사용

# 진료 대기 목록 페이지
@router.get("/consultation", response_class=HTMLResponse)
async def consultation_list(request: Request):
    # 하드코딩된 환자 리스트 (DB 연동 전 테스트용)
    consultations = [
        {
            "consultation_id": "c123",
            "name": "홍길동",
            "birth": "040201",
            "symptoms": "기침, 열",
            "requested_at": "2025-04-22 10:30"
        },
        {
            "consultation_id": "c124",
            "name": "김미소",
            "birth": "980912",
            "symptoms": "발진, 두드러기",
            "requested_at": "2025-04-22 11:00"
        }
    ]
    return templates.TemplateResponse("consultation_list.html", {
        "request": request,
        "consultations": consultations,
        "active_tab": "consultation"
    })

# 영상 진료 화면
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