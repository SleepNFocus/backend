from .base import *  # noqa

DEBUG = True  # 디버그 모드(개발 모드) 에러가 발생 하면 장고에서 노란 화면으로 알려줌

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "FocusZ",
        "USER": "dev_user",
        "PASSWORD": "sleepNfocus",
        "HOST": "localhost",
        "PORT": "54324",
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "USER_ID_FIELD": "user_id",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "BLACKLIST_AFTER_ROTATION": True,
    "ROTATE_REFRESH_TOKENS": True,
}
