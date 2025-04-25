from app.services.firestore_service import get_admin_by_id, get_doctor_by_id_and_department
from app.services.dynamodb_service import get_hospital_id_by_name  # 추가

async def process_login(public_health_center, role, department, password):
    role_map = {
        "의사": "doctor",
        "관리자": "admin"
    }
    mapped_role = role_map.get(role, role)

    hospital_id = get_hospital_id_by_name(public_health_center)
    if hospital_id is None:
        return {"error": "보건소 정보가 잘못되었습니다."}

    if mapped_role == "doctor":
        user = get_doctor_by_id_and_department(hospital_id, department)
        if user and user["password"] == password:
            return {"message": "로그인 성공"}

    elif mapped_role == "admin":
        user = get_admin_by_id(hospital_id)
        if user and user["password"] == password:
            return {"message": "로그인 성공"}

    return {"error": "아이디 또는 비밀번호가 올바르지 않습니다."}