from fastapi import FastAPI
from app.api import auth_routes
from app.api import doctor_routes
from app.api import prescription_routes
from app.api import admin_routes
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static", StaticFiles(directory="app/api/static"), name="static")

# 라우터 등록
app.include_router(auth_routes.router)
app.include_router(doctor_routes.router)
app.include_router(prescription_routes.router)
app.include_router(admin_routes.router)

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/login")

