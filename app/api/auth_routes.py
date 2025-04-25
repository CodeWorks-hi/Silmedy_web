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

# 🔒 기존 JSON용 모델 (유지)
class LoginRequest(BaseModel):
    public_health_center: str
    role: str
    department: str | None = None
    password: str

# ✅ 역할별 분리된 모델
class DoctorLoginRequest(BaseModel):
    public_health_center: str
    department: str
    password: str

class AdminLoginRequest(BaseModel):
    public_health_center: str
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

# ✅ 3. 의사 로그인 (Postman/API용)
@router.post("/api/login/doctor")
async def login_doctor_api(data: DoctorLoginRequest):
    result = await process_login(
        public_health_center=data.public_health_center,
        role="doctor",
        department=data.department,
        password=data.password
    )

    if result.get("message"):
        return {
            "status_code": status.HTTP_200_OK,
            "message": result["message"],
            "role": "doctor",
            "redirect_url": "/doctor/consultation"
        }

    return {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "error": result.get("error", "로그인 실패")
    }

# ✅ 4. 관리자 로그인 (Postman/API용)
@router.post("/api/login/admin")
async def login_admin_api(data: AdminLoginRequest):
    result = await process_login(
        public_health_center=data.public_health_center,
        role="admin",
        department=None,
        password=data.password
    )

    if result.get("message"):
        return {
            "status_code": status.HTTP_200_OK,
            "message": result["message"],
            "role": "admin",
            "redirect_url": "/admin/employees"
        }

    return {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "error": result.get("error", "로그인 실패")
    }