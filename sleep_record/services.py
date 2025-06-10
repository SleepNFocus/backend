from rest_framework.exceptions import ValidationError

from sleep_record.models import SleepRecord


def create_sleep_record(user, data):
    try:
        return SleepRecord.objects.create(
            user=user,
            date=data["date"],
            sleep_duration=data["sleep_duration"],
            subjective_quality=data["subjective_quality"],
            sleep_latency=data["sleep_latency"],
            wake_count=data["wake_count"],
            disturb_factors=data["disturb_factors"],
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
