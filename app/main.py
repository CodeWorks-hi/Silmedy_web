from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.services.firebase_service import init_firebase


# ✅ firebase_service는 import만 해도 내부에서 자동 초기화됨
from app.services import firebase_service

from app.api import auth_routes
from app.api import doctor_routes
from app.api import prescription_routes
from app.api import admin_routes
from app.api import common_routes

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/api/static"), name="static")

# 라우터 등록
app.include_router(auth_routes.router)
app.include_router(doctor_routes.router)
app.include_router(prescription_routes.router)
app.include_router(admin_routes.router)
app.include_router(common_routes.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/login")