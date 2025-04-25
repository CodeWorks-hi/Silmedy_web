from firebase_admin import firestore

def get_admin_by_id(hospital_id: int):
    doc_ref = firestore.client().collection("admins").document(str(hospital_id))
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None

# 의사 조회 (name → department 기준으로 수정)
# app/services/firestore_service.py

def get_doctor_by_id_and_department(hospital_id: int, department: str):
    docs = firestore.client().collection("doctors") \
        .where("hospital_id", "==", hospital_id) \
        .where("department", "==", department) \
        .stream()
    for doc in docs:
        return doc.to_dict()
    return None