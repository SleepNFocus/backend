# config/health_check.py
from typing import Any

from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    renderer_classes = [JSONRenderer]
    # 인증·권한 모두 해제 (외부에서 자유롭게 호출 가능)

    authentication_classes = []
    permission_classes = []

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # 단순 상태 확인용 응답
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
