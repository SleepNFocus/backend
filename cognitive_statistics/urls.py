from django.urls import path

from . import views

urlpatterns = [
    path(
        "result/basic/",
        views.CognitiveTestResultBasicAPIView.as_view(),
        name="cognitive-test-result-basic",
    ),
    path(
        "session/start/",
        views.CognitiveSessionCreateAPIView.as_view(),
        name="cognitive-session-start",
    ),
    path(
        "result/srt/",
        views.CognitiveResultSRTAPIView.as_view(),
        name="cognitive-result-srt",
    ),
    path(
        "result/pattern/",
        views.CognitiveResultPatternAPIView.as_view(),
        name="cognitive-result-pattern",
    ),
    path(
        "result/symbol/",
        views.CognitiveResultSymbolAPIView.as_view(),
        name="cognitive-result-symbol",
    ),
    path(
        "result/daily-summary/",
        views.CognitiveResultDailySummaryAPIView.as_view(),
        name="cognitive-result-daily-summary",
    ),
]
