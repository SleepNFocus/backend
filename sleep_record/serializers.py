from cognitive_statistics import serializers
from sleep_record.models import SleepRecord


class SleepCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SleepRecord
        fields = '__all__'

