async def process_login(public_health_center: str, role: str, department: str | None, password: str) -> dict:
    if role == "doctor" and password == "doctor123":
        return {"message": "로그인 성공"}
    elif role == "admin" and password == "doctor123":
        return {"message": "로그인 성공"}
    else:
        return {"error": "아이디 또는 비밀번호가 올바르지 않습니다."}