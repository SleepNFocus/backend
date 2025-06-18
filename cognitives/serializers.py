# 작성자: 한율
from rest_framework import serializers

from .models import CognitiveProblem


class CognitiveProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CognitiveProblem
        fields = ["id", "test_format", "parameters", "order"]


class TestAnswerSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    answer = serializers.JSONField()
    response_time_ms = serializers.IntegerField()


class TestSubmitSerializer(serializers.Serializer):
    answers = TestAnswerSerializer(many=True)
