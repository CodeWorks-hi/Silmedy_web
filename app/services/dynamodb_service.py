import boto3
import os
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

# ⚠️ 테이블 이름 정확히!
table_hospitals = dynamodb.Table("hospitals")

# 병원 이름으로 hospital_id 조회 함수
def get_all_hospitals():
    response = table_hospitals.scan()
    return response.get("Items", [])

def get_hospital_id_by_name(public_health_center: str):
    response = table_hospitals.scan(
        FilterExpression=Attr("name").eq(public_health_center)
    )
    items = response.get("Items", [])
    return items[0].get("hospital_id") if items else None