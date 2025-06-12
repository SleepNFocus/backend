# 작성자: 한율
from rest_framework import serializers

from sleep_record.models import SleepRecord


class SleepRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SleepRecord
        fields = "__all__"

        read_only_fields = ["id", "created_at", "updated_at"]
