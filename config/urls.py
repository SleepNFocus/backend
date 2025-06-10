from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import TemplateView
from django.conf import settings

urlpatterns = [
    path("", lambda request: HttpResponse("Hello, World!"), name="home"),
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/tests/", include("cognitives.urls")),
    path("api/cognitive-tests/", include("cognitive_statistics.urls")),
]


if settings.DEBUG:
    import yaml
    from rest_framework import permissions
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi

    # swagger.yaml 파일 로드
    with open('docs/swaggers/swagger.yaml', 'r', encoding='utf-8') as f:
        swagger_yaml = yaml.safe_load(f)

    info = swagger_yaml.get('info', {})
    schema_view = get_schema_view(
        openapi.Info(
            title=info.get('title', 'Checker API'),
            default_version=info.get('version', 'v1'),
            description=info.get('description', ''),
        ),
        url=swagger_yaml.get('servers', [{}])[0].get('url', ''),
        patterns=None,
        public=True,
        permission_classes=[permissions.AllowAny],
        generator_class=None,
    )

    urlpatterns += [
        path(
            'swagger/',
            schema_view.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui',
        ),
        path(
            'swagger.yaml',
            TemplateView.as_view(
                template_name='swaggers/swagger.yaml',   
                content_type='text/yaml',
            ),
            name='schema-yaml',
        ),
    ]
