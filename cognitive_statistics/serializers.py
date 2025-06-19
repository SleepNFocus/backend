from rest_framework import serializers

from .models import (
    CognitiveResultPattern,
    CognitiveResultSRT,
    CognitiveResultSymbol,
    CognitiveSession,
    CognitiveTestFormat,
)


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


class CognitiveTestResultDetailedSerializer(serializers.Serializer):
    detailed_raw_scores = serializers.SerializerMethodField()
    normalized_scores = serializers.JSONField()
    average_score = serializers.FloatField()  # DB의 average_score 필드를 그대로 노출
    total_duration_sec = serializers.IntegerField()

    def get_detailed_raw_scores(self, obj):
        session = obj.cognitive_session
        srt = CognitiveResultSRT.objects.filter(cognitive_session=session).first()
        sym = CognitiveResultSymbol.objects.filter(cognitive_session=session).first()
        pat = CognitiveResultPattern.objects.filter(cognitive_session=session).first()

        return {
            "srt": {
                "avg_ms": srt.reaction_avg_ms if srt else 0,
                "total_duration_sec": (srt.reaction_avg_ms * 10 // 1000) if srt else 0,
                "average_score": srt.score if srt else 0,
            },
            "symbol": {
                "correct": sym.symbol_correct if sym else 0,
                "avg_ms": sym.symbol_accuracy * 1000 if sym else 0,
                "symbol_accuracy": sym.symbol_accuracy if sym else 0,
                "total_duration_sec": sym.symbol_correct if sym else 0,
                "average_score": sym.score if sym else 0,
            },
            "pattern": {
                "correct": pat.pattern_correct if pat else 0,
                "total_duration_sec": int(pat.pattern_time_sec) if pat else 0,
                "average_score": pat.score if pat else 0,
            },
        }
