from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.services.auth_service import process_login

router = APIRouter()
templates = Jinja2Templates(directory="app/api/templates")

# 🧾 JSON 요청용 모델
class LoginRequest(BaseModel):
    public_health_center: str
    role: str
    department: str | None = None
    password: str


# 🔐 1. 브라우저 폼 로그인 화면 (GET)
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# 🧪 2. 브라우저 폼 제출 로그인 처리 (POST)
@router.post("/login")
async def login_form(
    request: Request,
    public_health_center: str = Form(...),
    role: str = Form(...),
    department: str = Form(None),
    password: str = Form(...)
):
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


# 📱 3. JSON 기반 API 로그인 (앱, Postman 등)
@router.post("/api/login")
async def login_api(request_data: LoginRequest):
    result = await process_login(
        public_health_center=request_data.public_health_center,
        role=request_data.role,
        department=request_data.department,
        password=request_data.password,
    )

    if result.get("message"):
        if request_data.role == "doctor":
            return RedirectResponse(url="/doctor/consultation", status_code=302)
        elif request_data.role == "admin":
            return RedirectResponse(url="/admin/employees", status_code=302)
        else:
            return {"message": "로그인 성공", "role": request_data.role}
    else:
        return {"error": result.get("error", "로그인 실패")}