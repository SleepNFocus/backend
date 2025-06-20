from rest_framework.exceptions import ValidationError

from sleep_record.models import SleepRecord


def create_sleep_record(user, data):
    try:

        if SleepRecord.objects.filter(user=user, date=data["date"]).exists():
            raise ValidationError("수면 기록을 이미 작성했습니다.")

        return SleepRecord.objects.create(
            user=user,
            date=data["date"],
            sleep_duration=data["sleep_duration"],
            subjective_quality=data["subjective_quality"],
            sleep_latency=data["sleep_latency"],
            wake_count=data["wake_count"],
            disturb_factors=data["disturb_factors"],
            score=calculate_sleep_score(data),
            memo=data["memo"],
        )

    except Exception as e:
        print("💥 수면 기록 생성 오류:", e)
        raise ValidationError({"detail": f"수면 기록 생성 실패: {str(e)}"})


def get_sleep_record(user, date):
    try:
        sleep_record = SleepRecord.objects.get(user=user, date=date)

        return sleep_record
    except Exception as e:
        print("💥 수면 기록 조회 오류:", e)
        raise ValidationError({"detail": f"수면 기록 조회 실패: {str(e)}"})


def update_sleep_record(user, data, date):

    try:
        sleep_record = SleepRecord.objects.get(user=user, date=date)

        sleep_record.sleep_duration = data["sleep_duration"]
        sleep_record.subjective_quality = data["subjective_quality"]
        sleep_record.sleep_latency = data["sleep_latency"]
        sleep_record.wake_count = data["wake_count"]
        sleep_record.disturb_factors = data["disturb_factors"]
        sleep_record.memo = data["memo"]

        sleep_record.score = calculate_sleep_score(data)

        sleep_record.save()

        return sleep_record
    except Exception as e:
        print("💥 수면 기록 수정 오류:", e)
        raise ValidationError({"detail": f"수면 기록 수정 실패: {str(e)}"})


def sleep_duration_score(minutes: int) -> int:
    if 420 <= minutes <= 540:
        return 25
    elif 390 <= minutes <= 570:
        return 20
    elif 360 <= minutes <= 600:
        return 15
    elif 330 <= minutes <= 630:
        return 10
    elif 300 <= minutes <= 660:
        return 5
    elif 270 <= minutes <= 690:
        return 0
    elif minutes <= 240 or minutes >= 720:
        return 0
    else:
        return 0


def subjective_quality_score(subjective_quality: int) -> int:
    mapping = {0: 0, 1: 10, 2: 20, 3: 25, 4: 30}
    return mapping.get(subjective_quality, 0)  # 잘못된 값은 0 처리


def sleep_latency_score(sleep_latency: int) -> int:
    if sleep_latency <= 15:
        return 15
    elif 15 < sleep_latency <= 30:
        return 10
    elif 30 < sleep_latency:
        return 0


def wake_count_score(wake_count: int) -> int:
    if wake_count == 0:
        return 10
    elif wake_count <= 2:
        return 5
    else:
        return 0


def disturb_factors_score(disturb_factors: list[str]) -> int:
    return max(0, 20 - 4 * len(disturb_factors))


def calculate_sleep_score(data: dict) -> int:
    score = (
        sleep_duration_score(data["sleep_duration"])
        + subjective_quality_score(data["subjective_quality"])
        + sleep_latency_score(data["sleep_latency"])
        + wake_count_score(data["wake_count"])
        + disturb_factors_score(data["disturb_factors"])
    )

    return min(score, 100)
