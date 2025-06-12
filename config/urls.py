import os

import yaml
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from config.health_check import HealthCheckView

# swagger.yaml 파일 읽기 (info 필드만 사용)
with open(os.path.join("docs", "swagger", "swagger.yaml"), "r") as f:
    swagger_dict = yaml.safe_load(f)

schema_view = get_schema_view(
    openapi.Info(
        title=swagger_dict["info"]["title"],
        default_version=swagger_dict["info"]["version"],
        description=swagger_dict["info"]["description"],
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url="https://www.dev.focusz.site",  # swagger.yaml의 servers URL
    patterns=[
        path("api/", include("management.urls")),
        path("api/", include("users.urls")),
        path("api/", include("sleep.urls")),
        path("api/", include("cognitives.urls")),
        path("api/", include("cognitive_statistics.urls")),
    ],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/cognitives/", include("cognitives.urls")),
    path("api/cognitive-statistics/", include("cognitive_statistics.urls")),
    path("api/", include("management.urls")),
    path("api/", include("users.urls")),
    path("api/", include("sleep.urls")),
    path("api/", include("cognitives.urls")),
    path("api/", include("cognitive_statistics.urls")),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("health/", HealthCheckView.as_view(), name="health-check"),
]
