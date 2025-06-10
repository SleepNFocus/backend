from django.conf import settings
from django.db import models


class CognitiveTestType(models.Model):

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class CognitiveTestFormat(models.Model):

    test_type = models.ForeignKey(
        CognitiveTestType, on_delete=models.CASCADE, related_name="formats"
    )
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    estimated_duration_sec = models.PositiveIntegerField(default=60)  # 권장 소요 시간
    order = models.PositiveIntegerField()  # 순차 실행 순서

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} ({self.test_type.name})"


class CognitiveTestTime(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cognitive_times",
    )
    test_format = models.ForeignKey(
        CognitiveTestFormat, on_delete=models.CASCADE, related_name="time_records"
    )
    duration_ms = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class CognitiveTestResult(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cognitive_results",
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    raw_scores = models.JSONField()
    normalized_scores = models.JSONField()
    average_score = models.FloatField()
    total_duration_sec = models.PositiveIntegerField()

    class Meta:
        ordering = ["-timestamp"]
