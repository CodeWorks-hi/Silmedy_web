from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.services.auth_service import process_login
from fastapi import status

router = APIRouter()
templates = Jinja2Templates(directory="app/api/templates")

# 🔁 역할 한글 ↔ 영문 코드 매핑
ROLE_MAP = {
    "의사": "doctor",
    "관리자": "admin",
    "환자": "patient"
}

# 📦 JSON 요청용 모델
class LoginRequest(BaseModel):
    public_health_center: str
    role: str
    department: str | None = None
    password: str

# 🖥 1. 브라우저용 로그인 페이지 렌더링
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 🖥 2. 브라우저 폼 제출용 로그인 처리
@router.post("/login")
async def login_form(
    request: Request,
    public_health_center: str = Form(...),
    role: str = Form(...),
    department: str = Form(None),
    password: str = Form(...)
):
    # 한글 role 처리
    role = ROLE_MAP.get(role, role)

    result = await process_login(public_health_center, role, department, password)

    if result.get("message"):
        if role == "doctor":
            return RedirectResponse(url="/doctor/consultation", status_code=302)
        elif role == "admin":
            return RedirectResponse(url="/admin/employees", status_code=302)
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": result.get("error", "로그인 실패")
        })

# 📱 3. 앱/테스트용 JSON 로그인 처리
@router.post("/api/login")
async def login_api(request_data: LoginRequest):
    role = ROLE_MAP.get(request_data.role, request_data.role)

    result = await process_login(
        public_health_center=request_data.public_health_center,
        role=role,
        department=request_data.department,
        password=request_data.password,
    )

    if result.get("message"):
        return {
            "status_code": status.HTTP_200_OK,
            "message": result["message"],
            "role": role,
            "redirect_url": f"/{role}/consultation" if role == "doctor" else f"/{role}/employees"
        }

    return {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "error": result.get("error", "로그인 실패")
    }