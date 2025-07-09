from django.urls import path

from ai.views import AIRecommendContentView

urlpatterns = [
    path(
        "recommendation/",
        AIRecommendContentView.as_view(),
        name="ai-content-recommendation",
    ),
]
