from fastapi import FastAPI
from app.api import auth_routes
from app.api import doctor_routes


app = FastAPI()

# 라우터 등록
app.include_router(auth_routes.router)
app.include_router(doctor_routes.router)

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/login")