import os

from .base import *  # noqa

DEBUG = True  # 디버그 모드(개발 모드) 에러가 발생 하면 장고에서 노란 화면으로 알려줌
ALLOWED_HOSTS = ["*"]

# 배포 환경에서는 CORS를 제한적으로 허용

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8081",
]
CORS_ALLOW_CREDENTIALS = True

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
