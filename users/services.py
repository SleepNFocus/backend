from django.db import transaction
from django.utils import timezone

from .models import User, UserBlacklist, UserStatus
from .utils import (
    generate_jwt_token_pair,
    get_access_token_from_code,
    get_google_user_info,
    get_kakao_user_info,
    normalize_profile_img,
)


# 유저 상태 관련 예외 처리용
class UserStatusException(Exception):
    pass


def get_or_create_active_user(provider, social_id, email, nickname, profile_img):
    # 소셜 타입 + 소셜 아이디로 기존 유저 조회
    user = User.objects.filter(
        social_type=provider.upper(), social_id=social_id
    ).first()
    # 블랙리스트 유저일 경우 로그인 거부
    if user:
        bl = UserBlacklist.objects.filter(user=user, is_active=True).first()
        if bl:
            raise UserStatusException(f"블랙리스트 계정: {bl.reason}")
        # 탈퇴 유저일 경우 기존 계정 비활성화 + 신규 계정 생성
        if user.status == UserStatus.WITHDRAWN or not user.is_active:
            # 탈퇴 유저 소셜 아이디 무력화
            user.social_id = (
                f"{user.social_id}_withdrawn_{int(timezone.now().timestamp())}"
            )
            # 무력화 된 아이디로 저장
            user.save(update_fields=["social_id"])

            # 새 계정 생성
            return User.objects.create(
                social_type=provider.upper(),
                social_id=social_id,
                email=email,
                nickname=nickname,
                profile_img=profile_img,
                joined_at=timezone.now(),
                status=UserStatus.ACTIVE,
                is_active=True,
            )
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
    return user


# 소셜 로그인 핸들러
class BaseSocialHandler:
    def get_access_token(self, code=None, access_token=None):
        raise NotImplementedError

    def get_user_info(self, access_token):
        raise NotImplementedError

    def extract_user_fields(self, user_info):
        raise NotImplementedError


# 카카오 소셜 로그인 핸들러
class KakaoHandler(BaseSocialHandler):
    def get_access_token(self, code=None, access_token=None):
        if code:
            return get_access_token_from_code("kakao", code)
        return access_token

    def get_user_info(self, access_token):
        return get_kakao_user_info(access_token)

    def extract_user_fields(self, user_info):
        social_id = str(user_info["id"])
        email = user_info.get("email")
        nickname = user_info.get("nickname")
        profile_img = normalize_profile_img("kakao", user_info.get("profile_img"))
        return social_id, email, nickname, profile_img


# 구글 소셜 로그인 핸들러
class GoogleHandler(BaseSocialHandler):
    def get_access_token(self, code=None, access_token=None):
        if code:
            return get_access_token_from_code("google", code)
        return access_token

    def get_user_info(self, access_token):
        return get_google_user_info(access_token)

    def extract_user_fields(self, user_info):
        social_id = str(user_info["sub"])
        email = user_info.get("email")
        nickname = user_info.get("name")
        profile_img = normalize_profile_img("google", user_info.get("profile_img"))
        return social_id, email, nickname, profile_img


# 소셜 로그인/자동 로그인 로직 처리
class SocialLoginService:
    handlers = {
        "kakao": KakaoHandler(),
        "google": GoogleHandler(),
    }

    # 소셜 로그인 처리 함수
    @classmethod
    def social_login(cls, provider, code=None, access_token=None):
        handler = cls.handlers.get(provider)
        if not handler:
            raise Exception("지원하지 않는 provider")

        access_token = handler.get_access_token(code, access_token)
        user_info = handler.get_user_info(access_token)
        social_id, email, nickname, profile_img = handler.extract_user_fields(user_info)

        user = get_or_create_active_user(
            provider, social_id, email, nickname, profile_img
        )

        user.last_login_at = timezone.now()
        user.save(update_fields=["last_login_at"])

        tokens = generate_jwt_token_pair(user)
        return tokens, user
