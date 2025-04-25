# # app/services/storage_service.py

# import firebase_admin
# from firebase_admin import storage
# import uuid

# def upload_profile_image(file_path: str, bucket_name: str = None) -> str:
#     if bucket_name is None:
#         bucket = storage.bucket()
#     else:
#         bucket = storage.bucket(bucket_name)

#     # 파일명 UUID로 생성
#     blob = bucket.blob(f"profile_images/{uuid.uuid4()}.png")
#     blob.upload_from_filename(file_path)
#     blob.make_public()  # 공개 URL로 접근 가능하도록

#     return blob.public_url

# app/services/storage_service.py

def upload_profile_image(path: str):
    return "https://dummy-image-url.com/test.jpg"