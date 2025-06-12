from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import UserStatus

from .serializers import (
    LogoutSerializer,
    OnboardingBasicSerializer,
    OnboardingJobSerializer,
    SocialLoginSerializer,
)
from .services import SocialLoginService
from .utils import add_token_to_blacklist, handle_social_login_error


# 소셜 로그인/자동 로그인
class SocialLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
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


# 로그아웃(리프레시 토큰 무효화)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # serializer로 유효성 검사
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 검사 통과 시 리프레시 토큰 꺼냄
        refresh_token = serializer.validated_data["refresh"]
        # 리프레시 토큰을 블랙리스트에 저장함
        add_token_to_blacklist(refresh_token)

        return Response({"message": "로그아웃 완료"}, status=200)


# 회원 탈퇴
class UserWithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.status = UserStatus.WITHDRAWN
        user.save()
        return Response({"message": "회원 탈퇴 완료"}, status=200)


# 온보딩 설문
# 기본 정보 저장
class OnboardingBasicView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OnboardingBasicSerializer(
            instance=request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(OnboardingBasicSerializer(user).data, status=200)


# 직업 설문 저장
class OnboardingJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OnboardingJobSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)
