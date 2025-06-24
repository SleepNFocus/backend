from collections import defaultdict
from datetime import date, datetime, timedelta

from django.db import transaction
from django.db.models import Avg, Sum
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from cognitive_statistics.models import (
    CognitiveResultPattern,
    CognitiveResultSRT,
    CognitiveResultSymbol,
    CognitiveSessionProblem,
)
from sleep_record.models import SleepRecord

from .models import User, UserBlacklist, UserStatus
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

        # [수정] 프로필 이미지에 값이 있을 때만 덮어쓰기
        if profile_img:  # [수정]
            user.profile_img = profile_img  # [수정]
            user.save()  # [수정]

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
            # 절대 url로 반환
            request.build_absolute_uri(user.profile_img.url)
            if user.profile_img and getattr(user.profile_img, "url", None)
            else None
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
# 날짜별 인지 점수 합산 (각 날짜별로 3종 테스트 점수 평균)
def get_daily_cognitive_scores(user, start_date, end_date):
    cognitive_data = defaultdict(list)  # 날짜별 점수 리스트 저장

    # 3가지 인지 테스트 결과 모델 반복
    cognitive_models = [
        CognitiveResultSRT,
        CognitiveResultPattern,
        CognitiveResultSymbol,
    ]
    for model in cognitive_models:
        # 해당 유저의 테스트 결과에서 기간 내 날짜, 점수만 가져옴
        results = model.objects.filter(
            cognitive_session__user=user, created_at__date__range=(start_date, end_date)
        ).values("created_at__date", "score")
        for r in results:
            date_key = r["created_at__date"]
            # date/datetime 타입 모두 지원
            if isinstance(date_key, datetime):
                date_key = date_key.date()
            cognitive_data[date_key].append(r["score"])

    # 날짜별 점수 평균값 계산
    daily_scores = {
        d: round(sum(scores) / len(scores), 1) for d, scores in cognitive_data.items()
    }
    return daily_scores


# 해당 유저의 기간 내 수면기록을 날짜별로 dict화
def get_sleep_records(user, start_date, end_date):
    return {
        r.date: r
        for r in SleepRecord.objects.filter(
            user=user, date__range=(start_date, end_date)
        )
    }


# 최근 90일간 일별 수면/인지 기록 리스트 조회
def get_record_day_list(user):
    today = timezone.now().date()
    start_date, end_date = today - timedelta(days=89), today  # 최근 90일 범위

    sleep_records = get_sleep_records(user, start_date, end_date)  # 날짜별 수면기록
    cognitive_scores = get_daily_cognitive_scores(
        user, start_date, end_date
    )  # 날짜별 인지점수

    results = []
    # 각 날짜마다 기록이 존재하는지 확인
    for single_date in daterange(start_date, end_date):  # end_date 포함
        sleep = sleep_records.get(single_date)
        cognitive_score = cognitive_scores.get(single_date)

        # 수면 or 인지 데이터 하나라도 있으면 결과에 추가
        if sleep or cognitive_score is not None:
            results.append(
                {
                    "date": str(single_date),  # 날짜 (문자열)
                    "sleep_hour": (
                        round(sleep.sleep_duration / 60, 1) if sleep else 0
                    ),  # 수면시간(시간단위)
                    "sleep_score": sleep.score if sleep else 0,  # 수면점수
                    "cognitive_score": (
                        cognitive_score if cognitive_score else 0
                    ),  # 인지점수
                }
            )

    # 데이터 없으면 에러 반환
    if not results:
        raise ValidationError("해당 기간 기록이 없습니다.")

    return results


# 최근 4주간 주별 수면/인지 기록 리스트 조회
def get_record_week_list(user):
    today = timezone.now().date()
    start_date, end_date = today - timedelta(weeks=3), today  # 최근 4주 범위

    sleep_records = get_sleep_records(user, start_date, end_date)  # 날짜별 수면기록

    results = []
    week_number = 1  # 주차 번호 (1부터)
    # 주별 구간 루프
    for week_start, week_end in weekrange(start_date, end_date):
        # 각 주에 해당하는 날짜별 수면 기록 모음
        weekly_sleeps = [
            sleep_records.get(d)
            for d in daterange(week_start, week_end)
            if sleep_records.get(d)
        ]
        # 각 주의 날짜별 인지점수 리스트 추출
        weekly_cognitive_scores = get_daily_cognitive_scores(
            user, week_start, week_end
        ).values()

        # 수면/인지 기록 모두 없으면 skip
        if not weekly_sleeps and not weekly_cognitive_scores:
            continue

        # 주간 총 수면시간(분 → 시간), 주간 평균 수면점수/인지점수
        total_sleep_minutes = sum(
            r.sleep_duration for r in weekly_sleeps if r.sleep_duration
        )
        avg_sleep_score = (
            round(
                sum(r.score for r in weekly_sleeps if r.score) / len(weekly_sleeps), 1
            )
            if weekly_sleeps
            else 0
        )
        avg_cognitive_score = (
            round(sum(weekly_cognitive_scores) / len(weekly_cognitive_scores), 1)
            if weekly_cognitive_scores
            else 0
        )

        # 결과 추가
        results.append(
            {
                "week": week_number,
                "start_date": week_start,
                "end_date": week_end,
                "total_sleep_hours": round(total_sleep_minutes / 60, 1),
                "average_sleep_score": avg_sleep_score,
                "average_cognitive_score": avg_cognitive_score,
            }
        )
        week_number += 1

    if not results:
        raise ValidationError("해당 기간 기록이 없습니다.")

    return results


# 최근 12개월간 월별 수면/인지 기록 리스트 조회
def get_record_month_list(user):
    today = timezone.now().date()
    results = []

    for i in range(12):
        # 월 시작, 끝 날짜 계산
        y, m = (today.year - (today.month - i - 1) // 12), (
            today.month - i - 1
        ) % 12 + 1
        month_start = date(y, m, 1)
        # 월 마지막날 구하기
        month_end = (
            date(y, m + 1, 1) - timedelta(days=1)
            if m != 12
            else date(y + 1, 1, 1) - timedelta(days=1)
        )

        # 해당 월 전체 수면기록/인지점수
        sleep_records = [
            r
            for r in SleepRecord.objects.filter(
                user=user, date__range=(month_start, month_end)
            )
        ]
        cognitive_scores = get_daily_cognitive_scores(
            user, month_start, month_end
        ).values()

        # 둘 다 없으면 건너뜀
        if not sleep_records and not cognitive_scores:
            continue

        # 월별 총 수면시간(시간), 평균 수면점수/인지점수
        sleep_hours = [r.sleep_duration / 60 for r in sleep_records if r.sleep_duration]
        sleep_scores = [r.score for r in sleep_records if r.score]

        results.append(
            {
                "month": f"{y}-{str(m).zfill(2)}",
                "total_sleep_hours": round(sum(sleep_hours), 1) if sleep_hours else 0,
                "average_sleep_score": (
                    round(sum(sleep_scores) / len(sleep_scores), 1)
                    if sleep_scores
                    else 0
                ),
                "average_cognitive_score": (
                    round(sum(cognitive_scores) / len(cognitive_scores), 1)
                    if cognitive_scores
                    else 0
                ),
            }
        )

    if not results:
        raise ValidationError("해당 기간 기록이 없습니다.")

    results.sort(key=lambda x: x["month"])  # 월 오름차순 정렬
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
    pattern_time_sec = pattern_qs.aggregate(avg=Avg("pattern_time_sec"))["avg"] or 0

    # 세션별로 첫 번째 결과만 사용해서 정확도 계산!!!!
    session_ids = pattern_qs.values_list("cognitive_session_id", flat=True).distinct()

    session_accuracy_list = []
    for session_id in session_ids:
        first_result = pattern_qs.filter(cognitive_session_id=session_id).first()
        if first_result:
            correct = first_result.pattern_correct
            total = CognitiveSessionProblem.objects.filter(
                session_id=session_id
            ).count()
            acc = correct / total if total else 0
            session_accuracy_list.append(acc)

    pattern_accuracy = (
        round(sum(session_accuracy_list) / len(session_accuracy_list) * 100, 1)
        if session_accuracy_list
        else 0
    )

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
        "pattern_time_ms": int(pattern_time_sec * 1000),
        "total_score": round(total_score, 1),
    }


# 전체 합친 최종 기록
def get_selected_date_detail(user, date):
    year, month = date.year, date.month

    graph = get_monthly_detail_date(user, year, month)
    graph["selected_date"] = str(date)

    sleep_detail = get_sleep_detail(user, date)
    cognitive_detail = get_cognitive_detail(user, date)

    sleep_detail = get_sleep_detail(user, date)
    cognitive_detail = get_cognitive_detail(user, date)

    # 수면/인지 둘 다 없을 때만 None
    if not sleep_detail and not cognitive_detail:
        return None

    # 수면 데이터가 없으면 기본값으로 대체
    detail = (
        sleep_detail
        if sleep_detail
        else {
            "date": str(date),
            "total_sleep_hours": 0,
            "sleep_score": 0,
        }
    )
    detail["cognitive_test"] = cognitive_detail

    return {
        "graph": graph,
        "detail": detail,
    }
