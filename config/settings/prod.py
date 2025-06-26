import os  # noqa

from .base import *  # noqa

DEBUG = False  # 디버그 모드(개발 모드) 에러가 발생 하면 장고에서 노란 화면으로 알려줌
ALLOWED_HOSTS = [
    "focusz.site",
    "www.focusz.site",  # *.focusz.site 전부 허용
    "dev.focusz.site",
    "www.dev.focusz.site",
]

# 배포 환경에서는 CORS를 제한적으로 허용

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8081",
    "https://focuz-admin.netlify.app",
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = ["https://focuz-admin.netlify.app", "http://localhost:8081"]

# DB는 .env 값 기반 설정 (이미 base.py에서 .env 로드됨)
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
}

# AWS_ACCESS_KEY_ID       = os.getenv("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY   = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")  # dev/prod 분기
AWS_S3_REGION_NAME = "ap-northeast-2"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_ADDRESSING_STYLE = "virtual"
AWS_DEFAULT_ACL = "public-read"
AWS_S3_FILE_OVERWRITE = False

MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/"
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
