# 작성자: 한율
import os  # noqa

from .base import *  # noqa

DEBUG = True  # 디버그 모드(개발 모드) 에러가 발생 하면 장고에서 노란 화면으로 알려줌
ALLOWED_HOSTS = ["*"]


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

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8081",  # 프론트 개발 서버
]

CORS_ALLOW_CREDENTIALS = True
