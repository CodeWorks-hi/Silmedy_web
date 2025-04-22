from fastapi import FastAPI
from app.api import auth_routes

app = FastAPI()

# 라우터 등록
app.include_router(auth_routes.router)