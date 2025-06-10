from cognitive_statistics import serializers
from sleep_record.models import SleepRecord


class SleepRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SleepRecord
        fields = "__all__"

        read_only_fields = ["id", "created_at", "updated_at"]
