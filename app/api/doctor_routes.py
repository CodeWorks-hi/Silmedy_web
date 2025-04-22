from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# 템플릿 경로 지정
templates = Jinja2Templates(directory="app/api/templates")
router = APIRouter(prefix="/doctor", tags=["Doctor"])

# 진료 대기 목록 페이지
@router.get("/consultation", response_class=HTMLResponse)
async def consultation_list(request: Request):
    # 🔧 테스트용 더미 데이터 (다음 단계에서 Firestore로 대체)
    consultations = [
        {
            "consultation_id": "c123",
            "patient_name": "홍길동",
            "symptoms": "기침, 열",
            "requested_at": "2025-04-22 10:30"
        },
        {
            "consultation_id": "c124",
            "patient_name": "김철수",
            "symptoms": "복통",
            "requested_at": "2025-04-22 10:40"
        }
    ]
    return templates.TemplateResponse("consultation_list.html", {
        "request": request,
        "consultations": consultations
    })

@router.get("/video-call/{consultation_id}", response_class=HTMLResponse)
async def video_call_page(request: Request, consultation_id: str):
    return templates.TemplateResponse("video_call.html", {
        "request": request,
        "consultation_id": consultation_id
    })