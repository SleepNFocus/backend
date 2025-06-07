from django.urls import path
from . import views

urlpatterns = [
    # 인지 기능 테스트 메타 정보 조회 (REQ-011 ~ REQ-012)
    path('problems/', views.CognitiveTestTypeListAPIView.as_view(), name='cognitive-test-types'),
    path('problems/types/', views.CognitiveTestFormatListAPIView.as_view(), name='cognitive-test-formats'),

    # 테스트 소요 시간 저장 및 권장 시간 안내 (REQ-014 ~ REQ-015)
    path('time/', views.CognitiveTestTimeSaveAPIView.as_view(), name='cognitive-test-time-save'),
    path('time/guide/', views.CognitiveTestTimeGuideAPIView.as_view(), name='cognitive-test-time-guide'),

    # 테스트 결과 조회 및 분석 (REQ-016 ~ REQ-018)
    path('result/basic/', views.CognitiveTestResultBasicAPIView.as_view(), name='cognitive-test-result-basic'),
    path('result/correlation/', views.CognitiveTestResultCorrelationAPIView.as_view(), name='cognitive-test-result-correlation'),
    path('result/visualization/', views.CognitiveTestResultVisualizationAPIView.as_view(), name='cognitive-test-result-visualization'),
]
