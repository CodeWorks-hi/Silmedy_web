# app/services/firebase_service.py

import firebase_admin
from firebase_admin import credentials
import os
from dotenv import load_dotenv

# 🔐 환경변수 로드
load_dotenv()

# ✅ Firebase 초기화 함수
def init_firebase():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if not cred_path or not os.path.exists(cred_path):
            raise FileNotFoundError(f"Firebase 서비스 계정 키가 없거나 잘못된 경로입니다: {cred_path}")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            "databaseURL": os.getenv("FIREBASE_DB_URL")
        })