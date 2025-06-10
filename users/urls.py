from typing import List, Union

from django.urls import path, URLPattern, URLResolver
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SocialLoginView

urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path('social-login/', SocialLoginView.as_view(), name='social-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]