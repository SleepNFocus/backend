from rest_framework import serializers

from .models import (
    CognitiveTestType,
    CognitiveTestFormat,
    CognitiveTestTime,
    CognitiveTestResult,
    CognitiveSession,
    CognitiveResultSRT,
    CognitiveResultPattern,
    CognitiveResultSymbol,

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


class CognitiveSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CognitiveSession
        fields = ["id", "started_at", "ended_at", "summary"]
        read_only_fields = ["id", "started_at", "ended_at", "summary"]


class CognitiveSessionWithProblemsSerializer(serializers.ModelSerializer):
    problems = serializers.SerializerMethodField()

    class Meta:
        model = CognitiveSession
        fields = ["id", "started_at", "ended_at", "summary", "problems"]

    def get_problems(self, obj):
        from cognitives.serializers import CognitiveProblemSerializer

        return CognitiveProblemSerializer(
            [sp.problem for sp in obj.problems.all()], many=True
        ).data


class CognitiveResultSRTSerializer(serializers.ModelSerializer):
    class Meta:
        model = CognitiveResultSRT
        fields = "__all__"


class CognitiveResultPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = CognitiveResultPattern
        fields = "__all__"


class CognitiveResultSymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = CognitiveResultSymbol
        fields = "__all__"
