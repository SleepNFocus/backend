# 작성자: 한율
from datetime import datetime

from rest_framework import serializers

from .models import JobSurvey, User


# 소셜 로그인(회원가입)
class SocialLoginSerializer(serializers.Serializer):
    provider: str = serializers.ChoiceField(
        choices=[("kakao", "KAKAO"), ("google", "GOOGLE")]
    )
    code: str = serializers.CharField(required=False, allow_blank=True)
    access_token: str = serializers.CharField(required=False, allow_blank=True)

    # code or access_token 중 하나만 필수

    def validate(self, data: dict) -> dict:
        code = data.get("code")
        access_token = data.get("access_token")

        if not code and not access_token:
            raise serializers.ValidationError(
                "code 또는 access_token 중 하나는 필수입니다."
            )
        if code and access_token:
            raise serializers.ValidationError(
                "code, access_token 중 하나만 입력해주세요."
            )
        return data


# 로그아웃(리프레시 토큰 무효화)
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        if not value:
            raise serializers.ValidationError("리프레시 토큰은 필수입니다.")
        return value


# 온보딩 설문
# 기본 정보 설문
class OnboardingBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["gender", "birth_year", "mbti"]

    # 출생 년도 선택 시 1900년도부터 현재 년도까지 제한
    def validate_birth_year(self, value):
        current_year = datetime.now().year
        if value is not None and (value < 1900 or value > current_year):
            raise serializers.ValidationError(
                "1900년부터 현재 년도 사이의 값을 선택해주세요."
            )
        return value

    # 기본 설문 정보 저장 시 db에 업데이트
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# 직업 설문
class OnboardingJobSerializer(serializers.ModelSerializer):
    cognitive_type_label = serializers.SerializerMethodField()
    work_time_pattern_label = serializers.SerializerMethodField()

    class Meta:
        model = JobSurvey
        fields = [
            "cognitive_type",
            "cognitive_type_label",
            "work_time_pattern",
            "work_time_pattern_label",
        ]

    # cognitive_type의 라벨을 같이 불러옴
    def get_cognitive_type_label(self, obj):
        return obj.get_cognitive_type_display()

    # work_time_pattern의 라벨을 같이 불러옴
    def get_work_time_pattern_label(self, obj):
        return obj.get_work_time_pattern_display()

    # 유저 정보와 설문 데이터로 설문 결과를 새로 저장
    def create(self, validated_data):
        user = self.context.get("request").user
        return JobSurvey.objects.create(user=user, **validated_data)


# 마이페이지 메인
class MypageMainSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    profile_img = serializers.URLField(
        allow_null=True,
        required=True
    )
    joined_at = serializers.DateTimeField()
    tracking_days = serializers.IntegerField()
    total_sleep_hours = serializers.FloatField()
    average_sleep_score = serializers.FloatField()
    average_cognitive_score = serializers.FloatField()