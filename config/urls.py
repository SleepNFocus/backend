from django.http import HttpResponse
from django.urls import path, include

urlpatterns = [
    path('', lambda request: HttpResponse('Hello, World!'), name='home'),

    path('api/tests/', include('cognitives.urls')),
    path('api/cognitive-tests/', include('cognitive_statistics.urls')),
]
