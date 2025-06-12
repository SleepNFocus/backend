from rest_framework import serializers

from cognitive_statistics.serializers import CognitiveTestFormatSerializer

from .models import CognitiveProblem


class CognitiveProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CognitiveProblem
        fields = ["id", "test_format", "parameters", "order"]


class TestPlayListSerializer(serializers.ModelSerializer):
    """
    /cognitives/ 에서 제공할 테스트 목록
    """

    class Meta:
        model = CognitiveTestFormatSerializer.Meta.model
        # CognitiveTestFormatSerializer 사용
        fields = CognitiveTestFormatSerializer.Meta.fields


class TestAnswerSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    answer = serializers.JSONField()
    response_time_ms = serializers.IntegerField()


class TestSubmitSerializer(serializers.Serializer):
    answers = TestAnswerSerializer(many=True)
