import redis
import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

# 레디스로 리프레시 토큰 블랙리스트 관리
# 레디스 서버에 연결
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)


def blacklist_refresh_token(token, exp):
    # 토큰을 블랙리스트에 만료시간 동안 저장
    redis_client.setex(f"blacklist:{token}", exp, "blacklisted")


def is_blacklisted(token):
    # 토큰이 블랙리스트에 있는지 확인 (있으면 True)
    return redis_client.exists(f"blacklist:{token}") == 1


# 최초 로그인 시 기본 프로필 이미지 url일 경우 null 처리
# 카카오 기본 프로필 이미지 URL
KAKAO_DEFAULT_IMG_URLS = [
    "http://img1.kakaocdn.net/thumb/R640x640.q70/?fname=http://t1.kakaocdn.net/account_images/default_profile.jpeg",
]
# 구글 기본 프로필 이미지에 포함되는 키워드
# 구글은 이미지가 고정 URL이 아님 그래서 특정 키워드가 포함된 경우만 골라냄
GOOGLE_DEFAULT_IMG_KEYWORDS = ["default_profile", "photo.jpg"]


def normalize_profile_img(provider, url):
    # url 없으면 none (db에는 null로 저장)
    if not url:
        return None
    # 카카오 기본 프로필 이미지면 none
    if provider == "kakao" and url in KAKAO_DEFAULT_IMG_URLS:
        return None
    # 구글 기본 이미지 키워드가 포함되어 있으면 none
    if provider == "google" and any(kw in url for kw in GOOGLE_DEFAULT_IMG_KEYWORDS):
        return None
    # 아무것도 해당되지 않으면 원래 url 반환
    return url


# 소셜 로그인 에러 응답 반환
def handle_social_login_error(detail):
    if "블랙리스트" in detail:
        reason = detail.split(":")[-1]
        return Response(
            {"detail": "블랙리스트 계정", "reason": reason},
            status=status.HTTP_403_FORBIDDEN,
        )
    elif "비활성" in detail or "탈퇴" in detail:
        return Response(
            {"detail": "비활성화/탈퇴 계정"}, status=status.HTTP_403_FORBIDDEN
        )
    elif "지원하지 않는 provider" in detail:
        return Response(
            {"detail": "지원하지 않는 provider"}, status=status.HTTP_400_BAD_REQUEST
        )
    else:
        return Response(
            {"detail": "소셜 로그인 실패", "error": detail},
            status=status.HTTP_400_BAD_REQUEST,
        )


# 소셜 인가 코드로 액세스 토큰 요청
def get_access_token_from_code(provider, code):
    if provider == "kakao":
        print("🟡 [Kakao 디버깅] 요청 직전 설정 확인:")
        print("    client_id:", settings.KAKAO_CLIENT_ID)
        print("    redirect_uri:", settings.KAKAO_REDIRECT_URI)
        print("    code:", code)
        # 카카오로 토큰 요청
        resp = requests.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_CLIENT_ID,
                "redirect_uri": settings.KAKAO_REDIRECT_URI,
                "code": code,
            },
            headers={"Content-type": "application/x-www-form-urlencoded"},
        )
        print("토큰 응답:", resp.status_code)
        print(resp.text)

        # 응답에서 액세스 토큰만 반환
        data = resp.json()
        if "access_token" not in data:
            raise Exception(f"Kakao 토큰 요청 실패: {data}")
        return data["access_token"]

    elif provider == "google":
        # 구글로 토큰 요청
        resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "code": code,
            },
        )
        data = resp.json()
        return data["access_token"]

    # 지원하지 않는 provider면 오류 발생
    else:
        raise Exception("지원하지 않는 provider")


# 카카오 엑세스 토큰으로 사용자 정보 요청
def get_kakao_user_info(access_token):
    resp = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    # 필요한 정보만 반환
    data = resp.json()
    # 디버깅 로그
    print("[디버깅로그] Kakao API response:", data)

    if "id" not in data:
        raise Exception(f"Kakao 응답에 'id' 없음: {data}")
    return {
        "id": data["id"],  # 카카오 고유 id
        "email": data["kakao_account"].get("email"),
        "nickname": data["properties"].get("nickname"),
        "profile_img": data["properties"].get("profile_image"),
    }


# 구글 액세스 토큰으로 사용자 정보 요청
def get_google_user_info(access_token):
    resp = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    # 필요한 정보만 반환
    data = resp.json()
    return {
        "sub": data["sub"],  # 구글 고유 id
        "email": data.get("email"),
        "name": data.get("name"),
        "profile_img": data.get("picture"),
    }


# 로그인 성공 유저에게 JWT 토큰 발급 (access/refresh)
def generate_jwt_token_pair(user):
    # 유저 기준으로 토큰 생성
    refresh = RefreshToken.for_user(user)
    # 둘 다 문자열로 반환
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


# 로그아웃(리프레시 토큰 무효화)
def add_token_to_blacklist(refresh_token):
    try:
        token = RefreshToken(refresh_token)

        jti = token.get("jti")  # 토큰 고유 id
        exp = token["exp"]
        now = token.current_time.timestamp()

        timeout = int(exp - now)  # 토큰이 앞으로 몇 초 동안 유효한지
        cache.set(
            f"blacklist:{jti}", "true", timeout
        )  # 레디스에 어떻게 저장하고 언제 삭제할건지

    except Exception:
        pass  # 유효하지 않은 토큰일 경우 무시


# mbti 선택안함 시 db에 null로 처리
def normalize_mbti(value):
    if value == "선택안함":
        return None
    return value
