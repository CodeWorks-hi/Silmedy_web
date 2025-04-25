# app/api/common_routes.py

from fastapi import APIRouter, UploadFile, File, Body
# from app.services.storage_service import upload_profile_image
from app.services.fcm_service import send_push_notification

router = APIRouter()

# @router.post("/api/upload-profile")
# async def upload_profile(file: UploadFile = File(...)):
#     temp_path = f"/tmp/{file.filename}"
#     with open(temp_path, "wb") as buffer:
#         buffer.write(await file.read())

#     url = upload_profile_image(temp_path)
#     return {
#         "status_code": 200,
#         "message": "업로드 성공",
#         "url": url
#     }

@router.post("/api/send-notification")
async def push_notification(
    token: str = Body(...),
    title: str = Body(...),
    body: str = Body(...),
    data: dict = Body(default={})
):
    response = send_push_notification(token, title, body, data)
    return {
        "status_code": 200,
        "message": "푸시 알림 전송됨",
        "fcm_response": response
    }