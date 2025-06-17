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
    estimated_duration_sec = models.PositiveIntegerField(default=60)
    order = models.PositiveIntegerField()

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
    test_format = models.ForeignKey(
        CognitiveTestFormat,
        on_delete=models.CASCADE,
        related_name="results",
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    raw_scores = models.JSONField()
    normalized_scores = models.JSONField()
    average_score = models.FloatField()
    total_duration_sec = models.PositiveIntegerField()

    class Meta:
        ordering = ["-timestamp"]


class CognitiveSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cognitive_sessions",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    summary = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - Session from {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}"


class CognitiveSessionProblem(models.Model):
    session = models.ForeignKey(
        "CognitiveSession", on_delete=models.CASCADE, related_name="problems"
    )
    problem = models.ForeignKey("cognitives.CognitiveProblem", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("session", "problem")

    def __str__(self):
        return f"{self.session_id} - {self.problem_id}"


class CognitiveResultSRT(models.Model):
    cognitive_session = models.ForeignKey("CognitiveSession", on_delete=models.CASCADE)
    score = models.IntegerField()
    reaction_avg_ms = models.FloatField()
    reaction_list = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class CognitiveResultPattern(models.Model):
    cognitive_session = models.ForeignKey("CognitiveSession", on_delete=models.CASCADE)
    score = models.IntegerField()
    pattern_correct = models.IntegerField()
    pattern_time_sec = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)


class CognitiveResultSymbol(models.Model):
    cognitive_session = models.ForeignKey("CognitiveSession", on_delete=models.CASCADE)
    score = models.IntegerField()
    symbol_correct = models.IntegerField()
    symbol_accuracy = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
