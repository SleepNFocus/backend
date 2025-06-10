from typing import Any
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, UserBlacklist
from .serializers import SocialLoginSerializer
from .utils import (
    generate_jwt_token_pair,
    get_access_token_from_code,
    get_google_user_info,
    get_kakao_user_info,
    normalize_profile_img,
)


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

        # 인가 코드 있으면 엑세스 토큰 요청
        if code:
            try:
                access_token = get_access_token_from_code(provider, code)
            except Exception as e:
                # 발급 실패 시 에러 응답
                return Response(
                    {"detail": "소셜 엑세스 토큰 발급 실패", "error": str(e)},
                    status=400,
                )

        # 카카오로 사용자 정보 조회 및 필드 가져오기
        if provider == "kakao":
            user_info = get_kakao_user_info(access_token)
            social_id = str(user_info["id"])
            email = user_info["email"]
            nickname = user_info["nickname"]
            # 기본 프로필 이미지일 경우 none
            profile_img = normalize_profile_img("kakao", user_info.get("profile_img"))

        # 구글로 사용자 정보 조회 및 필드 가져오기
        elif provider == "google":
            user_info = get_google_user_info(access_token)
            social_id = user_info["sub"]
            email = user_info["email"]
            nickname = user_info["name"]
            profile_img = normalize_profile_img("google", user_info.get("profile_img"))

        # 다른 provider일 경우 에러 반환
        else:
            return Response({"detail": "지원하지 않는 provider"}, status=400)

        # 소셜 타입 + 소셜 아이디로 기존 유저 조회
        user = User.objects.filter(
            social_type=provider.upper(), social_id=social_id
        ).first()
        # 블랙리스트 유저일 경우 로그인 거부
        if user:
            bl = UserBlacklist.objects.filter(user=user, is_active=True).first()
            if bl:
                return Response(
                    {"detail": "블랙리스트 계정", "reason": bl.reason}, status=403
                )
            # 탈퇴/비활성 유저 거부
            if not user.is_active or user.status != "active":
                return Response({"detail": "비활성/탈퇴 계정"}, status=403)
        # 유저가 없으면 회원가입
        if not user:
            with transaction.atomic():
                user = User.objects.create(
                    social_type=provider.upper(),
                    social_id=social_id,
                    email=email,
                    nickname=nickname,
                    profile_img=profile_img,
                    joined_at=timezone.now(),
                    status="active",
                    is_active=True,
                )

        # 마지막 로그인 시각 갱신 및 저장
        user.last_login_at = timezone.now()
        user.save(update_fields=["last_login_at"])

        # JWT 토큰 발급 (access/refresh)
        tokens = generate_jwt_token_pair(user)

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
