# 작성자: 한율
from rest_framework import serializers

from sleep_record.models import SleepRecord


class SleepRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SleepRecord
        fields = [
            "date",
            "sleep_duration",
            "subjective_quality",
            "sleep_latency",
            "wake_count",
            "disturb_factors",
            "memo",
            "created_at",
            "updated_at",
        ]

        read_only_fields = ["id", "created_at", "updated_at"]
