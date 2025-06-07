from django.urls import path
from . import views

urlpatterns = [
    path('', views.TestPlayListAPIView.as_view(), name='test-play-list'),
    path('<str:test_type>/', views.TestPlayAPIView.as_view(), name='test-play'),
    path('<str:test_type>/submit/', views.TestSubmitAPIView.as_view(), name='test-submit'),
]
