from django.contrib.postgres.fields import ArrayField
from django.db import models

from users.models import User


class SleepRecord(models.Model):
    id = models.AutoField(primary_key=True, db_column="sleep_record_id")
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    date = models.DateField()
    sleep_duration = models.IntegerField()
    subjective_quality = models.IntegerField()
    sleep_latency = models.IntegerField()
    wake_count = models.IntegerField()
    disturb_factors = ArrayField(
        models.CharField(max_length=255),
        blank=True,
        default=list,
        help_text="수면 방해 요소 리스트",
    )
    score = models.IntegerField()
    memo = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sleep_record"
