# 작성자: 한율
from typing import List, Union

from django.urls import URLPattern, URLResolver, path

from management.views import (
    AdminLogsView,
    AdminRootView,
    AdminUserDetailView,
    AdminUserListView,
)

urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("admin", AdminRootView.as_view(), name="admin_root"),
    path("admin/users", AdminUserListView.as_view(), name="admin_user_list"),
    path(
        "admin/users/<int:pk>", AdminUserDetailView.as_view(), name="admin_user_detail"
    ),
    path("admin/logs", AdminLogsView.as_view(), name="admin_logs"),
]
