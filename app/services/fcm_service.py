# app/services/fcm_service.py

from firebase_admin import messaging

def send_push_notification(token: str, title: str, body: str, data: dict = {}):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token,
        data={k: str(v) for k, v in data.items()}  # data는 string만 허용
    )

    response = messaging.send(message)
    return response