from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

router = APIRouter(prefix="/doctor", tags=["Doctor"])
templates = Jinja2Templates(directory="app/api/templates")

# ✅ 하드코딩된 진료 목록 (공통으로 사용)
dummy_consultations = [
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

# ✅ 기존 웹 페이지: 대기 목록
@router.get("/consultation", response_class=HTMLResponse)
async def consultation_list(request: Request):
    return templates.TemplateResponse("consultation_list.html", {
        "request": request,
        "consultations": dummy_consultations,
        "active_tab": "consultation"
    })

# ✅ 기존 웹 페이지: 영상 진료 화면
@router.get("/video-call/{consultation_id}", response_class=HTMLResponse)
async def video_call_page(request: Request, consultation_id: str):
    # 진료 ID에 따라 하드코딩된 데이터 반환
    consultation = next((c for c in dummy_consultations if c["consultation_id"] == consultation_id), {
        "consultation_id": consultation_id,
        "patient_id": "p001",
        "doctor_id": "d001",
        "previous_date": "2024-01-10",
        "previous_disease_code": "DIS001"
    })

    patient = {
        "name": consultation.get("name", "홍길동"),
        "birth": consultation.get("birth", "040324"),
        "gender": "남",
        "symptom_area": "목",
        "main_symptom": consultation.get("symptoms", "기침")
    }

    return templates.TemplateResponse("video_call.html", {
        "request": request,
        "consultation_id": consultation_id,
        "consultation": consultation,
        "patient": patient,
        "active_tab": "video"
    })

# ✅ Postman용 JSON API: 대기 목록 조회
@router.get("/consultation/json")
async def get_consultation_list():
    return {
        "status_code": 200,
        "message": "대기 진료 목록 조회 성공",
        "data": dummy_consultations
    }

# ✅ Postman용 JSON API: 영상진료 연결
class VideoRequest(BaseModel):
    consultation_id: str

@router.post("/video-call/json")
async def start_video_call(data: VideoRequest):
    consultation = next((c for c in dummy_consultations if c["consultation_id"] == data.consultation_id), None)

    if not consultation:
        return {
            "status_code": 404,
            "error": "해당 ID의 진료 내역이 없습니다."
        }

    patient = {
        "name": consultation["name"],
        "birth": consultation["birth"],
        "gender": "남",
        "symptom_area": "목",
        "main_symptom": consultation["symptoms"]
    }

    return {
        "status_code": 200,
        "message": f"{data.consultation_id} 영상진료방 연결됨",
        "consultation": consultation,
        "patient": patient,
        "room_url": f"/doctor/video-call/{data.consultation_id}"
    }