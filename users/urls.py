from typing import List, Union

from django.urls import URLPattern, URLResolver, path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LogoutView,
    OnboardingBasicView,
    OnboardingJobView,
    SocialLoginView,
    UserWithdrawalView,
)

urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("social-login/", SocialLoginView.as_view(), name="social-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("withdrawal/", UserWithdrawalView.as_view(), name="withdrawal"),
    path("onboarding/basic/", OnboardingBasicView.as_view(), name="onboarding-basic"),
    path("onboarding/job/", OnboardingJobView.as_view(), name="onboarding-job"),
]
