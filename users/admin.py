from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    # 꼭 필요한 정보
    list_display = [
        "user_id",
        "email",
        "nickname",
        "social_type",
        "gender",
        "birth_year",
        "status",
        "is_active",
        "joined_at",
    ]
    # 검색
    search_fields = ["email", "nickname", "social_id"]
    # 사이드바 필터
    list_filter = ["social_type", "status", "is_active"]
    # 최신 가입순
    ordering = ["-joined_at"]
    # 날짜 정보 (읽기 전용으로 수정 불가)
    readonly_fields = ["joined_at", "updated_at", "last_login_at"]
