import os

from .base import *  # noqa

# 로컬 개발 서버는 언제나 모든 호스트 허용
ALLOWED_HOSTS = ["*"]

# 로컬 환경에서는 모든 origin 허용
CORS_ALLOW_ALL_ORIGINS = True

# 로컬 DB는 .env 기반 설정 (이미 base.py에서 로드됨)
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DB_NAME", "FocusZ"),
        "USER": os.getenv("DB_USER", "focusz"),
        "PASSWORD": os.getenv("DB_PASSWORD", "sleepNfocus"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "54324"),
        "OPTIONS": {
            "client_encoding": "UTF8",
        },
    }
}
