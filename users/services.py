from collections import defaultdict
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Avg, Sum
from django.utils import timezone

from cognitive_statistics.models import (
    CognitiveResultPattern,
    CognitiveResultSRT,
    CognitiveResultSymbol,
)
from sleep_record.models import SleepRecord

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


# 마이페이지 메인 요약 정보
def get_mypage_main_data(user):
    # 모든 수면 기록
    sleep_records = SleepRecord.objects.filter(user=user)

    # 수면 관련
    tracking_days = sleep_records.count()
    total_sleep_minutes = (
        sleep_records.aggregate(total=Sum("sleep_duration"))["total"] or 0
    )
    total_sleep_hours = round(total_sleep_minutes / 60, 1)
    average_sleep_score = sleep_records.aggregate(avg=Avg("score"))["avg"] or 0.0

    # 인지 관련
    # SRT
    srt_avg = (
        CognitiveResultSRT.objects.filter(cognitive_session__user=user).aggregate(
            avg=Avg("score")
        )["avg"]
        or 0.0
    )
    # Pattern
    pattern_avg = (
        CognitiveResultPattern.objects.filter(cognitive_session__user=user).aggregate(
            avg=Avg("score")
        )["avg"]
        or 0.0
    )
    # Symbol
    symbol_avg = (
        CognitiveResultSymbol.objects.filter(cognitive_session__user=user).aggregate(
            avg=Avg("score")
        )["avg"]
        or 0.0
    )

    # 세 점수의 평균 구하기 (3개 다 있으면 3으로 나누고 일부만 있으면 일부 개수로 나눔)
    cognitive_avgs = [v for v in [srt_avg, pattern_avg, symbol_avg] if v > 0]
    if cognitive_avgs:
        average_cognitive_score = round(sum(cognitive_avgs) / len(cognitive_avgs), 1)
    else:
        average_cognitive_score = 0.0

    return {
        "nickname": user.nickname,
        "profile_img": user.profile_img,
        "joined_at": user.joined_at,
        "tracking_days": tracking_days,
        "total_sleep_hours": total_sleep_hours,
        "average_sleep_score": round(average_sleep_score, 1),
        "average_cognitive_score": average_cognitive_score,
    }


# 마이페이지 기록 조회 (리스트뷰)
# 공통 날짜 매핑용
def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)


# 날짜별로 SRT/Pattern/Symbol 점수 합산
def get_daily_cognitive_scores(user, start_date, end_date):
    daily_scores = defaultdict(float)

    # SRT
    srt_scores = (
        CognitiveResultSRT.objects.filter(
            cognitive_session__user=user, created_at__date__range=(start_date, end_date)
        )
        .values("created_at__date")
        .annotate(score=Avg("score"))
    )
    for r in srt_scores:
        daily_scores[r["created_at__date"]] += r["score"] or 0

    # Pattern
    pattern_scores = (
        CognitiveResultPattern.objects.filter(
            cognitive_session__user=user, created_at__date__range=(start_date, end_date)
        )
        .values("created_at__date")
        .annotate(score=Avg("score"))
    )
    for r in pattern_scores:
        daily_scores[r["created_at__date"]] += r["score"] or 0

    # Symbol
    symbol_scores = (
        CognitiveResultSymbol.objects.filter(
            cognitive_session__user=user, created_at__date__range=(start_date, end_date)
        )
        .values("created_at__date")
        .annotate(score=Avg("score"))
    )
    for r in symbol_scores:
        daily_scores[r["created_at__date"]] += r["score"] or 0

    return daily_scores


# 일별 기록 (최근 3개월, 90일)
def get_record_day_list(user):
    # 수면/인지 기록 조회 (90일 기준)
    today = timezone.now().date()
    start_date = today - timedelta(days=89)
    end_date = today

    # 해당 기간의 수면 기록 조회 (date별로 연결)
    sleep_records = {
        r.date: r
        for r in SleepRecord.objects.filter(
            user=user, date__range=(start_date, end_date)
        )
    }
    # 해당 기간의 날짜별 인지 점수 합산
    cognitive_scores = get_daily_cognitive_scores(user, start_date, end_date)

    results = []
    # 기간 내 각 날짜별로 집계
    for d in daterange(start_date, end_date):
        sr = sleep_records.get(d)
        cs = cognitive_scores.get(d)
        # 수면/인지 기록이 하나라도 있으면 결과 추가
        if sr or cs is not None:
            results.append(
                {
                    "date": d,
                    "sleep_hour": round((sr.sleep_duration if sr else 0) / 60, 1),
                    "sleep_score": round(sr.score, 1) if sr else 0,
                    "cognitive_score": round(cs, 1) if cs is not None else 0,
                }
            )
    return results


# 주별 기록 (최근 4주)
def get_record_week_list(user):
    # 주별 기록 조회 (4주 기준)
    today = timezone.now().date()
    start_date = today - timedelta(days=27)
    end_date = today

    sleep_records = {
        r.date: r
        for r in SleepRecord.objects.filter(
            user=user, date__range=(start_date, end_date)
        )
    }
    daily_scores = get_daily_cognitive_scores(user, start_date, end_date)

    results = []
    week_num = 1
    d = start_date
    while d <= end_date:
        week_start = d
        week_end = min(d + timedelta(days=6), end_date)
        week_dates = list(daterange(week_start, week_end))

        sleep_hours = []
        sleep_scores = []
        cog_scores = []

        for wd in week_dates:
            sr = sleep_records.get(wd)
            cs = daily_scores.get(wd)
            if sr:
                sleep_hours.append((sr.sleep_duration or 0) / 60)
                sleep_scores.append(sr.score)
            if cs is not None:
                cog_scores.append(cs)

        if sleep_hours or sleep_scores or cog_scores:
            results.append(
                {
                    "week": week_num,
                    "start_date": week_start,
                    "end_date": week_end,
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
        week_num += 1
        d = week_end + timedelta(days=1)
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
    return results
