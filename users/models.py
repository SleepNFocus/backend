from typing import Any

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


# User ENUM 필드
class SocialType(models.TextChoices):
    KAKAO = "KAKAO"
    GOOGLE = "GOOGLE"


class Gender(models.TextChoices):
    MALE = "남"
    FEMALE = "여"


class MBTIType(models.TextChoices):
    ISTJ = "ISTJ"
    ISFJ = "ISFJ"
    INTJ = "INTJ"
    INFJ = "INFJ"
    ISTP = "ISTP"
    ISFP = "ISFP"
    INTP = "INTP"
    INFP = "INFP"
    ESTJ = "ESTJ"
    ESFJ = "ESFJ"
    ENTJ = "ENTJ"
    ENFJ = "ENFJ"
    ESTP = "ESTP"
    ESFP = "ESFP"
    ENTP = "ENTP"
    ENFP = "ENFP"
    NONE = "선택안함"


class UserStatus(models.TextChoices):
    ACTIVE = "active"
    DORMANT = "dormant"
    WITHDRAWN = "withdrawn"


# Jobsurvey ENUM 필드
class CognitiveType(models.TextChoices):
    HIGH_FOCUS = "high_focus"
    MULTITASK = "multitask"
    PHYSICAL = "physical"
    NONE = "none"


class WorkTimePattern(models.TextChoices):
    REGULAR_DAY = "regular_day"
    SHIFT_NIGHT = "shift_night"
    FLEXIBLE = "flexible"
    NO_SCHEDULE = "no_schedule"


# 커스텀 유저 매니저
class CustomUserManager(BaseUserManager["User"]):
    def create_user(
        self, email: str, social_type: str, social_id: str, **extra_fields: Any
    ) -> "User":
        if not email:
            raise ValueError("이메일은 필수 항목입니다.")
        email = self.normalize_email(email)
        user = self.model(
            email=email, social_id=social_id, social_type=social_type, **extra_fields
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        social_type: str = "KAKAO",
        social_id: str = "admin",
        **extra_fields: Any,
    ) -> "User":
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        return self.create_user(email, social_type, social_id, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    user_id: int = models.AutoField(primary_key=True)
    social_type: str = models.CharField(max_length=20, choices=SocialType.choices)
    social_id: str = models.CharField(max_length=255, unique=True)
    email: str = models.EmailField(max_length=100)
    nickname: str = models.CharField(max_length=50)
    profile_img: str | None = models.TextField(null=True, blank=True)
    gender: str = models.CharField(max_length=5, choices=Gender.choices)
    birth_year: int = models.PositiveSmallIntegerField()
    mbti: str | None = models.CharField(
        max_length=10, choices=MBTIType.choices, null=True, blank=True
    )
    joined_at: timezone.datetime = models.DateTimeField(default=timezone.now)
    last_login_at: timezone.datetime | None = models.DateTimeField(
        null=True, blank=True
    )
    updated_at: timezone.datetime = models.DateTimeField(auto_now=True)
    status: str = models.CharField(
        max_length=10, choices=UserStatus.choices, default=UserStatus.ACTIVE
    )
    is_active: bool = models.BooleanField(default=True)
    is_admin: bool = models.BooleanField(default=False)
    is_staff: bool = models.BooleanField(default=False)

    USERNAME_FIELD = "social_id"
    REQUIRED_FIELDS = ["social_type", "email", "nickname"]

    objects = CustomUserManager()

    def __str__(self) -> str:
        return f"{self.nickname} - {self.email} / {self.social_type}"


class UserBlacklist(models.Model):
    blacklist_id: int = models.AutoField(primary_key=True)
    user: User = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blacklists"
    )
    reason: str | None = models.TextField(null=True, blank=True)
    created_at: timezone.datetime = models.DateTimeField(default=timezone.now)
    expired_at: timezone.datetime | None = models.DateTimeField(null=True, blank=True)
    is_active: bool = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.user.nickname} - {self.reason or '사유 미기재'}"


class JobSurvey(models.Model):
    job_survey_id: int = models.AutoField(primary_key=True)
    user: User = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="job_surveys"
    )
    cognitive_type: str = models.CharField(max_length=20, choices=CognitiveType.choices)
    work_time_pattern: str = models.CharField(
        max_length=20, choices=WorkTimePattern.choices
    )
    created_at: timezone.datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return (
            f"{self.user.nickname} - {self.cognitive_type} / {self.work_time_pattern}"
        )
