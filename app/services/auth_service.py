# Firebase 연동 로직이 추가될 예정
async def process_login(phc, role, department, password):
    # ⚠️ 실제로는 Firebase 또는 Firestore에서 사용자 정보를 조회해야 함
    if role == "admin" and password == "doctor123":
        return {"message": "관리자 로그인 성공"}
    elif role == "doctor" and department and password == "doctor123":
        return {"message": f"{department} 의사 로그인 성공"}
    else:
        return {"error": "로그인 실패"}