from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

urlpatterns = [
    path("", lambda request: HttpResponse("Hello, World!"), name="home"),
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/tests/", include("cognitives.urls")),
    path("api/cognitive-tests/", include("cognitive_statistics.urls")),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    # 🔐 JWT 토큰 발급/갱신 엔드포인트
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # 각 앱 API 연결
    path("api/sleepRecord/", include("sleep_record.urls")),
]
