# 작성자: 한율
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from config.health_check import HealthCheckView

urlpatterns = [
    path("", lambda request: HttpResponse("Hello, World!"), name="home"),
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/cognitives/", include("cognitives.urls")),
    path("api/cognitive-statistics/", include("cognitive_statistics.urls")),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    # 🔐 JWT 토큰 발급/갱신 엔드포인트
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # 각 앱 API 연결
    path("api/sleepRecord/", include("sleep_record.urls")),
]
