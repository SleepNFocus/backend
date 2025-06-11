from rest_framework import serializers

from users.models import User


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "user_id",
            "email",
            "nickname",
            "gender",
            "birth_year",
            "status",
            "is_active",
            "is_admin",
            "joined_at",
            "last_login_at",
            "updated_at",
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["user_id", "is_admin", "email", "nickname"]
        read_only_fields = ["user_id"]

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        instance.nickname = validated_data.get("nickname", instance.nickname)
        instance.is_admin = validated_data.get("is_admin", instance.is_admin)
        instance.save()
        return instance
