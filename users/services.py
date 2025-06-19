from collections import defaultdict
from datetime import date, timedelta

from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Avg, Sum
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from cognitive_statistics.models import (
    CognitiveResultPattern,
    CognitiveResultSRT,
    CognitiveResultSymbol,
)
from sleep_record.models import SleepRecord

from .models import User, UserBlacklist, UserStatus, SleepRecord
from .utils import (
    daterange,
    download_and_save_profile_image,
    generate_jwt_token_pair,
    get_access_token_from_code,
    get_google_user_info,
    get_kakao_user_info,
    normalize_profile_img,
    weekrange,
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
        # 기존 이미지가 있으면 덮지 않음
        if user.profile_img:
            profile_img = user.profile_img

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


# 마이페이지 메인 요약 정보
def get_mypage_main_data(user, request):
    # 탈퇴한 계정일 경우 마이페이지 접근 차단
    if user.status == UserStatus.WITHDRAWN:
        raise PermissionDenied("탈퇴된 유저입니다.")

    # 모든 수면 기록
    sleep_records = SleepRecord.objects.filter(user=user)

    # 수면 관련
    tracking_days = sleep_records.count()
    total_sleep_minutes = (
        sleep_records.aggregate(total=Sum("sleep_duration"))["total"] or 0
    )
    total_sleep_hours = round(total_sleep_minutes / 60, 1)

    # score가 모두 null일 수 있으므로 None 처리 방어
    avg_score = sleep_records.aggregate(avg=Avg("score"))["avg"]
    average_sleep_score = round(avg_score, 1) if avg_score is not None else 0.0

    # 90일치 일별 인지 점수(평균)
    today = timezone.now().date()
    start_date = today - timedelta(days=89)
    end_date = today
    cognitive_scores = get_daily_cognitive_scores(user, start_date, end_date)
    cognitive_score_list = list(cognitive_scores.values())

    if cognitive_score_list:
        average_cognitive_score = round(
            sum(cognitive_score_list) / len(cognitive_score_list), 1
        )
    else:
        average_cognitive_score = 0.0

    return {
        "nickname": user.nickname,
        "profile_img": (
            # 수정: 절대 URL로 반환되도록 처리
            request.build_absolute_uri(user.profile_img.url)
            if hasattr(user.profile_img, "url")
            and default_storage.exists(user.profile_img.name)
            else str(user.profile_img) if user.profile_img else None
        ),
        "joined_at": user.joined_at if user.joined_at else None,
        "tracking_days": tracking_days,
        "total_sleep_hours": total_sleep_hours,
        "average_sleep_score": average_sleep_score,
        "average_cognitive_score": average_cognitive_score,
    }


# 사용자 정보 가져온 뒤 프로필 이미지 처리
def create_or_update_user_by_social(
    provider, social_id, email, nickname, profile_img_url
):
    user, created = User.objects.get_or_create(
        social_type=provider,
        social_id=social_id,
        defaults={
            "nickname": nickname,
            "email": email,
            "status": UserStatus.ACTIVE,
        },
    )

    if created:
        # 소셜 url 이미지가 기본 이미지면 None 처리
        profile_img_url = normalize_profile_img(provider, profile_img_url)

        # 소셜 url 이미지가 유효하면 서버에 저장
        download_and_save_profile_image(user, profile_img_url)
    return user


# 마이페이지 기록 조회 (리스트뷰)
# 날짜별 인지 점수 합산
def get_daily_cognitive_scores(user, start_date, end_date):
    daily_srt = defaultdict(list)
    daily_pattern = defaultdict(list)
    daily_symbol = defaultdict(list)

    # SRT
    for r in CognitiveResultSRT.objects.filter(
        cognitive_session__user=user, created_at__date__range=(start_date, end_date)
    ).values("created_at__date", "score"):
        daily_srt[r["created_at__date"]].append(r["score"])

    # Pattern
    for r in CognitiveResultPattern.objects.filter(
        cognitive_session__user=user, created_at__date__range=(start_date, end_date)
    ).values("created_at__date", "score"):
        daily_pattern[r["created_at__date"]].append(r["score"])

    # Symbol
    for r in CognitiveResultSymbol.objects.filter(
        cognitive_session__user=user, created_at__date__range=(start_date, end_date)
    ).values("created_at__date", "score"):
        daily_symbol[r["created_at__date"]].append(r["score"])

    # 날짜별 평균 계산
    daily_scores = {}
    all_dates = set(daily_srt) | set(daily_pattern) | set(daily_symbol)

    for d in all_dates:
        scores = []
        for lst in [
            daily_srt.get(d, []),
            daily_pattern.get(d, []),
            daily_symbol.get(d, []),
        ]:
            if lst:
                scores.append(sum(lst) / len(lst))
        if scores:
            daily_scores[d] = sum(scores) / len(scores)  # [각 테스트별 평균]의 평균
    return daily_scores


# 일별 (최근 7일)
def get_record_day_list(user):
    today = date.today()
    start_date = today - timedelta(days=6)
    end_date = today

    # 유저의 최근 7일 수면 기록 조회 후 date를 문자열로 키 설정
    sleep_records = {
        str(r.date): r
        for r in SleepRecord.objects.filter(user=user, date__range=(start_date, end_date))
    }

    results = []
    for d in daterange(start_date, end_date):
        date_str = str(d)  # 날짜 문자열 변환
        sleep = sleep_records.get(date_str)

        results.append({
            "date": date_str,
            "total_sleep_hours": round((sleep.sleep_duration or 0) / 60, 1) if sleep else 0,
            "sleep_score": sleep.score if sleep else 0,
            "cognitive_score": 0,  # 인지 점수 로직 제거 후 기본값 0 반환
        })
    return results

# 주별 (최근 4주)
def get_record_week_list(user):
    today = date.today()
    start_date = today - timedelta(weeks=3)
    end_date = today

    # 유저의 최근 4주 수면 기록 조회 후 date를 문자열로 키 설정
    sleep_records = {
        str(r.date): r
        for r in SleepRecord.objects.filter(user=user, date__range=(start_date, end_date))
    }

    results = []
    for week_start, week_end in weekrange(start_date, end_date):  # 튜플 언팩 지원하도록 변경된 weekrange 사용
        week_dates = list(daterange(week_start, week_end))
        normalized_dates = [str(d if isinstance(d, date) else d.date()) for d in week_dates]  # 날짜 문자열 변환

        weekly_sleeps = [sleep_records.get(d) for d in normalized_dates if sleep_records.get(d)]

        total_sleep_minutes = sum(r.sleep_duration for r in weekly_sleeps if r and r.sleep_duration)
        avg_sleep_score = (
            sum(r.score for r in weekly_sleeps if r and r.score is not None) / len(weekly_sleeps)
            if weekly_sleeps else 0
        )

        results.append({
            "week": f"{week_start} ~ {week_end}",
            "total_sleep_hours": round(total_sleep_minutes / 60, 1),
            "average_sleep_score": round(avg_sleep_score, 1),
            "average_cognitive_score": 0,  # 인지 점수 로직 제거 후 기본값 0 반환
        })

    return results


# 월별 (최근 1년, 12개월)
def get_record_month_list(user):
    # 월별 기록 조회 (12개월 기준)
    today = timezone.now().date()
    results = []
    for i in range(12):
        # 해당 월의 시작/끝 날짜 계산
        y = today.year if today.month - i > 0 else today.year - 1
        m = (today.month - i) % 12 or 12
        month_start = date(y, m, 1)
        if m == 12:
            month_end = date(y + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(y, m + 1, 1) - timedelta(days=1)

        # 수면 기록 월별 조회
        sleep_records = [
            r
            for r in SleepRecord.objects.filter(
                user=user, date__range=(month_start, month_end)
            )
        ]

        # 해당 월의 모든 날짜별 인지 점수 구하기
        daily_scores = get_daily_cognitive_scores(user, month_start, month_end)
        # 점수만 리스트로 추출 (월 전체)
        cog_scores = [score for score in daily_scores.values()]

        # 월별 수면 시간/점수 리스트
        sleep_hours = [(r.sleep_duration or 0) / 60 for r in sleep_records]
        sleep_scores = [r.score for r in sleep_records]

        # 데이터가 하나라도 있으면 결과 추가
        if sleep_hours or sleep_scores or cog_scores:
            results.append(
                {
                    "month": f"{y}-{str(m).zfill(2)}",
                    "total_sleep_hours": (
                        round(sum(sleep_hours), 1) if sleep_hours else 0
                    ),
                    "average_sleep_score": (
                        round(sum(sleep_scores) / len(sleep_scores), 1)
                        if sleep_scores
                        else 0
                    ),
                    "average_cognitive_score": (
                        round(sum(cog_scores) / len(cog_scores), 1) if cog_scores else 0
                    ),
                }
            )
            # 오름차순으로 결과 정렬
    results.sort(key=lambda x: x["month"])

    # 모든 결과가 0이면 기록 없음 예외 처리
    if not results or all(
        (r["total_sleep_hours"] == 0 and r["average_cognitive_score"] == 0)
        for r in results
    ):
        raise ValidationError("해당 기간 기록이 없습니다.")

    return results


# 마이페이지 선택 날짜 상세 조회
# 월 전체 그래프 데이터
def get_monthly_detail_date(user, year, month):
    # 월 시작/끝 날짜
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)

    # 날짜별 데이터 집계
    date_list = []
    sleep_hour_list = []
    sleep_score_list = []
    cognitive_score_list = []

    sleep_records = {
        r.date: r
        for r in SleepRecord.objects.filter(
            user=user, date__range=(month_start, month_end)
        )
    }
    cognitive_scores = get_daily_cognitive_scores(user, month_start, month_end)

    for d in daterange(month_start, month_end):
        date_list.append(d)
        sr = sleep_records.get(d)
        cs = cognitive_scores.get(d)
        sleep_hour_list.append(round((sr.sleep_duration if sr else 0) / 60, 1))
        sleep_score_list.append(round(sr.score, 1) if sr else 0)
        cognitive_score_list.append(round(cs, 1) if cs is not None else 0)

    return {
        "dates": [str(d) for d in date_list],
        "sleep_hour_list": sleep_hour_list,
        "sleep_score_list": sleep_score_list,
        "cognitive_score_list": cognitive_score_list,
    }


# 해당 날짜 수면 상세 기록
def get_sleep_detail(user, date):
    sr = SleepRecord.objects.filter(user=user, date=date).first()
    if not sr:
        return None
    return {
        "date": str(date),
        "total_sleep_hours": (
            round(sr.sleep_duration / 60, 1) if sr.sleep_duration else 0
        ),
        "sleep_score": round(sr.score, 1) if sr.score else 0,
    }


# 해당 날짜의 인지 기록 상세
def get_cognitive_detail(user, date):
    srt_qs = CognitiveResultSRT.objects.filter(
        cognitive_session__user=user, created_at__date=date
    )
    pattern_qs = CognitiveResultPattern.objects.filter(
        cognitive_session__user=user, created_at__date=date
    )
    symbol_qs = CognitiveResultSymbol.objects.filter(
        cognitive_session__user=user, created_at__date=date
    )

    srt_score = srt_qs.aggregate(avg=Avg("score"))["avg"] or 0
    srt_time_ms = srt_qs.aggregate(avg=Avg("reaction_avg_ms"))["avg"] or 0

    symbol_score = symbol_qs.aggregate(avg=Avg("score"))["avg"] or 0
    symbol_count = symbol_qs.aggregate(total=Sum("symbol_correct"))["total"] or 0
    symbol_accuracy = symbol_qs.aggregate(avg=Avg("symbol_accuracy"))["avg"] or 0

    pattern_score = pattern_qs.aggregate(avg=Avg("score"))["avg"] or 0
    pattern_count = pattern_qs.aggregate(total=Sum("pattern_correct"))["total"] or 0
    # 정확도가 없기 때문에 0으로 고정, 필요하다면 따로 계산
    pattern_accuracy = 0
    pattern_time_sec = pattern_qs.aggregate(avg=Avg("pattern_time_sec"))["avg"] or 0

    total_score = srt_score + symbol_score + pattern_score

    return {
        "srt_score": round(srt_score, 1),
        "srt_time_ms": int(srt_time_ms),
        "symbol_score": round(symbol_score, 1),
        "symbol_count": int(symbol_count),
        "symbol_accuracy": int(symbol_accuracy),
        "pattern_score": round(pattern_score, 1),
        "pattern_count": int(pattern_count),
        "pattern_accuracy": int(pattern_accuracy),
        "pattern_time_ms": int(pattern_time_sec * 1000),  # 초 → 밀리초 변환
        "total_score": round(total_score, 1),
    }


# 전체 합친 최종 기록
def get_selected_date_detail(user, date):
    year, month = date.year, date.month

    graph = get_monthly_detail_date(user, year, month)
    graph["selected_date"] = str(date)

    sleep_detail = get_sleep_detail(user, date)
    cognitive_detail = get_cognitive_detail(user, date)
    if not sleep_detail:
        return None

    detail = sleep_detail
    detail["cognitive_test"] = cognitive_detail

    return {
        "graph": graph,
        "detail": detail,
    }
