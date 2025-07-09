from django.db import models

from cognitive_statistics.models import CognitiveSession
from sleep_record.models import SleepRecord


class ContentRecommendation(models.Model):
    id = models.AutoField(primary_key=True, db_column="content_recommendation_id")
    cognitive = models.ForeignKey(
        CognitiveSession, on_delete=models.CASCADE, db_column="cognitive_session_id"
    )
    recommend_reason = models.TextField()
    recommend_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content_recommendation"


class SleepScorePrediction(models.Model):
    id = models.AutoField(primary_key=True, db_column="sleep_score_prediction_id")
    sleep_record = models.ForeignKey(
        SleepRecord, on_delete=models.CASCADE, db_column="sleep_record_id"
    )
    record_date = models.DateTimeField(auto_now_add=True)
    predicted_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sleep_score_prediction"
