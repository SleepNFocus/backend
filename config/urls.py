# 작성자: 한율
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
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
    path("api/", include("management.urls")),
]


if settings.DEBUG:
    import yaml
    from drf_yasg import openapi
    from drf_yasg.views import get_schema_view
    from rest_framework import permissions

    with open("docs/swagger/swagger.yaml", "r", encoding="utf-8") as f:
        swagger_yaml = yaml.safe_load(f)

    info = swagger_yaml.get("info", {})
    schema_view = get_schema_view(
        openapi.Info(
            title=info.get("title", "Checker API"),
            default_version=info.get("version", "v1"),
            description=info.get("description", ""),
        ),
        url=swagger_yaml.get("servers", [{}])[0].get("url", ""),
        patterns=None,
        public=True,
        permission_classes=[permissions.AllowAny],
        generator_class=None,
    )

    urlpatterns += [
        path(
            "swagger/",
            schema_view.with_ui("swagger", cache_timeout=0),
            name="schema-swagger-ui",
        ),
        path(
            "swagger.yaml",
            TemplateView.as_view(
                template_name="swagger/swagger.yaml",
                content_type="text/yaml",
            ),
            name="schema-yaml",
        ),
    ]
