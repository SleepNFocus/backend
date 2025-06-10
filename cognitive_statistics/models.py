from django.db import models

from users.models import User


class CognitiveSession(models.Model):
    id = models.AutoField(primary_key=True, db_column="cognitive_session_id")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    total_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cognitive_session"
