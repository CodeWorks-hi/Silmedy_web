async def process_login(public_health_center: str, role: str, department: str | None, password: str) -> dict:
    # 🔐 실제 DB 또는 Firebase 연동 처리 여기에 넣으면 됨
    # 아래는 예시
    if role == "doctor" and password == "닥터123":
        return {"message": "로그인 성공"}
    elif role == "admin" and password == "어드민123":
        return {"message": "로그인 성공"}
    else:
        return {"error": "아이디 또는 비밀번호가 올바르지 않습니다."}