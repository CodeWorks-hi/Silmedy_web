from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.auth_service import process_login
from fastapi.responses import RedirectResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/api/templates")

# 로그인 페이지 랜더링
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_submit(
    request: Request,
    public_health_center: str = Form(...),
    role: str = Form(...),
    department: str = Form(None),
    password: str = Form(...)
):
    result = await process_login(public_health_center, role, department, password)

    # 로그인 성공 → 역할별 페이지 리디렉션
    if result.get("message"):
        if role == "doctor":
            return RedirectResponse(url="/doctor/consultation", status_code=302)
        elif role == "admin":
            return RedirectResponse(url="/admin/dashboard", status_code=302)  # 아직 없음
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": result.get("error", "로그인 실패"),
        })