from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.auth_service import process_login

router = APIRouter()
templates = Jinja2Templates(directory="app/api/templates")

# 로그인 페이지 랜더링
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 로그인 처리 (POST)
@router.post("/login")
async def login_submit(
    request: Request,
    public_health_center: str = Form(...),
    role: str = Form(...),
    department: str = Form(None),
    password: str = Form(...)
):
    # 로그인 로직 호출
    result = await process_login(public_health_center, role, department, password)
    return {"result": result}