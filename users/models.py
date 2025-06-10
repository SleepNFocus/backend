from __future__ import annotations

from typing import Any

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


# User ENUM 필드 (선택지 제한용)
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
    # 일반 사용자
    def create_user(
        self, email: str, social_type: str, social_id: str, **extra_fields: Any
    ) -> "User":
        if not email:
            raise ValueError("이메일은 필수 항목입니다.")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            social_id=social_id,
            social_type=social_type,
            **extra_fields,
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    # 관리자
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


# User
class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    social_type = models.CharField(max_length=20, choices=SocialType.choices)
    social_id = models.CharField(max_length=255)
    email = models.EmailField(max_length=100)
    nickname = models.CharField(max_length=50)
    profile_img = models.TextField(null=True, blank=True)
    gender = models.CharField(
        max_length=5, choices=Gender.choices, null=True, blank=True
    )
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    mbti = models.CharField(
        max_length=10, choices=MBTIType.choices, null=True, blank=True
    )  # 시리얼라이저에서 null로 변환 처리
    joined_at = models.DateTimeField(default=timezone.now)
    last_login_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=10, choices=UserStatus.choices, default=UserStatus.ACTIVE
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "user_id"
    REQUIRED_FIELDS = ["social_type", "email", "nickname", "gender", "birth_year"]

    objects = CustomUserManager()

    def __str__(self) -> str:
        return f"{self.nickname} - {self.email} / {self.social_type}"

    # 소셜 타입 + 소셜 아이디 유니크 조합 설정
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["social_type", "social_id"], name="unique_social_type_id"
            )
        ]


# UserBlacklist
class UserBlacklist(models.Model):
    blacklist_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blacklists")
    reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    expired_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.user.nickname} - {self.reason or '사유 미기재'}"


# JobSurvey
class JobSurvey(models.Model):
    job_survey_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="job_surveys")
    cognitive_type = models.CharField(max_length=20, choices=CognitiveType.choices)
    work_time_pattern = models.CharField(max_length=20, choices=WorkTimePattern.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return (
            f"{self.user.nickname} - {self.cognitive_type} / {self.work_time_pattern}"
        )
