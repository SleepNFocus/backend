from typing import Any

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SocialLoginSerializer
from .services import SocialLoginService
from .utils import handle_social_login_error


# 소셜 로그인/자동 로그인
class SocialLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        # serializer로 데이터 검사
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data["provider"]
        code = serializer.validated_data.get("code")
        access_token = serializer.validated_data.get("access_token")

        try:
            tokens, user = SocialLoginService.social_login(
                provider=provider, code=code, access_token=access_token
            )
        except Exception as e:
            # 함수로 에러 메세지 반환
            return handle_social_login_error(str(e))

        # 토큰/유저 정보 응답
        return Response(
            {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": {
                    "user_id": user.user_id,
                    "social_type": user.social_type,
                    "social_id": user.social_id,
                    "nickname": user.nickname,
                    "email": user.email,
                    "profile_img": user.profile_img,
                    "status": user.status,
                },
            },
            status=200,
        )
