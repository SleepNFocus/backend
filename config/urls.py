from django.http import HttpResponse
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users.views import CustomTokenObtainPairView

urlpatterns = [
    path("", lambda request: HttpResponse("Hello, World!"), name="home"),
    path("api/tests/", include("cognitives.urls")),
    path("api/cognitive-tests/", include("cognitive_statistics.urls")),
    # 🔐 JWT 토큰 발급/갱신 엔드포인트
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # 각 앱 API 연결
    path("api/sleepRecord/", include("sleep_record.urls")),
]
