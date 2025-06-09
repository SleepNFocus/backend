from django.db import models
from django.conf import settings
from cognitive_statistics.models import CognitiveTestFormat

class CognitiveProblem(models.Model):
    """
    문제은행 모델 (각 테스트 형식별 문제)
    """
    test_format = models.ForeignKey(
        CognitiveTestFormat,
        on_delete=models.CASCADE,
        related_name='problems'
    )
    # 테스트 클라이언트에 전달할 임의 JSON 파라미터
    parameters = models.JSONField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'Problem #{self.pk} for {self.test_format.name}'


class CognitiveResponse(models.Model):
    """
    사용자의 개별 문제 응답 기록
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cognitive_responses'
    )
    problem = models.ForeignKey(
        CognitiveProblem,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    submitted_answer = models.JSONField()
    response_time_ms = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']