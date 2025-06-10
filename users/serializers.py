from rest_framework import serializers

from .models import User


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