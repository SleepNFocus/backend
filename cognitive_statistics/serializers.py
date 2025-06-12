from rest_framework import serializers

from .models import (
    CognitiveTestFormat,
    CognitiveTestResult,
    CognitiveTestTime,
    CognitiveTestType,
)


class CognitiveTestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CognitiveTestType
        fields = ["id", "name", "description"]


class CognitiveTestFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = CognitiveTestFormat
        fields = [
            "id",
            "test_type",
            "name",
            "description",
            "estimated_duration_sec",
            "order",
        ]


class CognitiveTestTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CognitiveTestTime
        fields = ["id", "test_format", "duration_ms", "created_at"]
        read_only_fields = ["id", "created_at"]


class CognitiveTestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CognitiveTestResult
        fields = [
            "id",
            "timestamp",
            "raw_scores",
            "normalized_scores",
            "average_score",
            "total_duration_sec",
        ]
        read_only_fields = ["id", "timestamp"]
