from rest_framework.exceptions import ValidationError

from sleep_record.models import SleepRecord


def create_sleep_record(user, data):
    try:
        print("💤 disturb_factors 타입:", type(data["disturb_factors"]))
        return SleepRecord.objects.create(
            user=user,
            date=data["date"],
            sleep_duration=data["sleep_duration"],
            subjective_quality=data["subjective_quality"],
            sleep_latency=data["sleep_latency"],
            wake_count=data["wake_count"],
            disturb_factors=data["disturb_factors"],
        )

    except Exception as e:
        print("💥 수면 기록 생성 오류:", e)
        raise ValidationError({"detail": f"수면 기록 생성 실패: {str(e)}"})
