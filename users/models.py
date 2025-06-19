from __future__ import annotations

from datetime import datetime
from typing import Any

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# 출생년도 유효성 검사용 함수 (birth_year에 사용)
def validate_birth_year(value):
    # 현재 연도를 가져옴
    current_year = datetime.now().year
    # 출생년도가 1900년보다 작거나 현재 연도보다 크면 에러
    if value < 1900 or value > current_year:
        raise ValidationError(f"1900년부터 {current_year}년 사이로 입력해주세요.")


# User ENUM 필드 (선택지 제한용)
class SocialType(models.TextChoices):
    KAKAO = "KAKAO"
    GOOGLE = "GOOGLE"


class Gender(models.TextChoices):
    MALE = "남"
    FEMALE = "여"
    NONE = "선택안함"


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
    HIGH_FOCUS = (
        "high_focus",
        "복잡한 문제 해결·전략적 사고 중심",
    )
    MULTITASK = (
        "multitask",
        "판단력·멀티태스킹·정보 처리 중심",
    )
    PHYSICAL = (
        "physical",
        "반복적 업무·신체 활동 중심",
    )
    NONE = "none", "현재 일하지 않음 / 학생 / 은퇴 등"


class WorkTimePattern(models.TextChoices):
    REGULAR_DAY = "regular_day", "낮 시간대, 규칙적 근무"
    SHIFT_NIGHT = "shift_night", "교대/야간 등 불규칙 근무"
    FLEXIBLE = "flexible", "자유로운 시간대, 프리랜서 등"
    NO_SCHEDULE = "no_schedule", "일정 없음 / 학생 / 주부 등"


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
    profile_img = models.ImageField(upload_to="profile/", null=True, blank=True)
    gender = models.CharField(
        max_length=5, choices=Gender.choices, null=True, blank=True
    )
    birth_year = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[validate_birth_year]
    )
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
    REQUIRED_FIELDS = ["social_type", "email", "nickname"]

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
