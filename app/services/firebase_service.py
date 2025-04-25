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
        cred_path = os.path.join("secrets", "firebase-service-account.json")
        if not os.path.exists(cred_path):
            raise FileNotFoundError("Firebase 서비스 계정 키가 없습니다.")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)