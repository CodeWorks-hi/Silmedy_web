from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="app/api/templates")

@router.get("/employees", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("admin_employees.html", {"request": request, "active_tab": "employees"})

@router.get("/manage", response_class=HTMLResponse)
async def manage_page(request: Request):
    return templates.TemplateResponse("admin_manage.html", {"request": request, "active_tab": "manage"})