from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

router = APIRouter()
templates = Jinja2Templates(directory="app/api/templates")

# 기존 HTML 기반 관리자 화면
@router.get("/admin/employees", response_class=HTMLResponse)
async def admin_employees(request: Request):
    employees = [
        {"name": "김현수", "email": "hkim@example.com", "department": "내과"},
        {"name": "이서연", "email": "slee@example.com", "department": "소아과"},
    ]
    return templates.TemplateResponse("admin_employees.html", {
        "request": request,
        "employees": employees
    })

@router.get("/admin/manage", response_class=HTMLResponse)
async def admin_manage_page(request: Request):
    return templates.TemplateResponse("admin_manage.html", {"request": request})

# ✅ JSON 기반 직원 목록 API
@router.get("/api/admin/employees")
async def get_employees_api():
    employees = [
        {"name": "김현수", "email": "hkim@example.com", "department": "내과"},
        {"name": "이서연", "email": "slee@example.com", "department": "소아과"},
    ]
    return {
        "status_code": 200,
        "message": "직원 목록 조회 완료",
        "data": employees
    }

# ✅ JSON 기반 관리자 페이지 안내
@router.get("/api/admin/manage")
async def get_admin_manage_api():
    return {
        "status_code": 200,
        "message": "관리자 설정 페이지 (개발 예정)"
    }