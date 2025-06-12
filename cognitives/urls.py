# 작성자: 한율
from typing import List, Union

from django.urls import URLPattern, URLResolver, path

from . import views

urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("", views.TestPlayListAPIView.as_view(), name="test-play-list"),
    path("<str:test_type>/", views.TestPlayAPIView.as_view(), name="test-play"),
    path(
        "<str:test_type>/submit/", views.TestSubmitAPIView.as_view(), name="test-submit"
    ),
]
