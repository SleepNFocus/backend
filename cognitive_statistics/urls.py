# 작성자: 한율
from django.urls import path

from . import views
from .views import CognitiveSessionCreateAPIView

urlpatterns = [
    path(
        "problems/",
        views.CognitiveTestTypeListAPIView.as_view(),
        name="cognitive-test-types",
    ),
    path(
        "problems/types/",
        views.CognitiveTestFormatListAPIView.as_view(),
        name="cognitive-test-formats",
    ),
    path(
        "time/",
        views.CognitiveTestTimeSaveAPIView.as_view(),
        name="cognitive-test-time-save",
    ),
    path(
        "time/guide/",
        views.CognitiveTestTimeGuideAPIView.as_view(),
        name="cognitive-test-time-guide",
    ),
    path(
        "result/basic/",
        views.CognitiveTestResultBasicAPIView.as_view(),
        name="cognitive-test-result-basic",
    ),
    path(
        "result/correlation/",
        views.CognitiveTestResultCorrelationAPIView.as_view(),
        name="cognitive-test-result-correlation",
    ),
    path(
        "result/visualization/",
        views.CognitiveTestResultVisualizationAPIView.as_view(),
        name="cognitive-test-result-visualization",
    ),
    path(
        "session/start/",
        CognitiveSessionCreateAPIView.as_view(),
        name="cognitive-session-start",
    ),
]
