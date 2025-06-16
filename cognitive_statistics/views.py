# cognitive_statistics/views.py
from random import randint

from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    CognitiveSession,
    CognitiveSessionProblem,
    CognitiveTestFormat,
    CognitiveTestResult,
    CognitiveTestTime,
    CognitiveTestType,
)
from .serializers import (
    CognitiveSessionWithProblemsSerializer,
    CognitiveTestFormatSerializer,
    CognitiveTestResultSerializer,
    CognitiveTestTimeSerializer,
    CognitiveTestTypeSerializer,
    CognitiveResultSRTSerializer,
    CognitiveResultPatternSerializer,
    CognitiveResultSymbolSerializer,


)
from cognitives.models import CognitiveProblem


class CognitiveTestTypeListAPIView(generics.ListAPIView):
    queryset = CognitiveTestType.objects.all()
    serializer_class = CognitiveTestTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class CognitiveTestFormatListAPIView(generics.ListAPIView):
    queryset = CognitiveTestFormat.objects.select_related("test_type").all()
    serializer_class = CognitiveTestFormatSerializer
    permission_classes = [permissions.IsAuthenticated]


class CognitiveTestTimeSaveAPIView(generics.CreateAPIView):
    serializer_class = CognitiveTestTimeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CognitiveTestTimeGuideAPIView(generics.ListAPIView):
    queryset = CognitiveTestFormat.objects.all()
    serializer_class = CognitiveTestFormatSerializer
    permission_classes = [IsAuthenticated]


class CognitiveTestResultBasicAPIView(generics.ListAPIView):
    serializer_class = CognitiveTestResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CognitiveTestResult.objects.filter(user=self.request.user)


class CognitiveTestResultCorrelationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"detail": "Correlation feature not implemented yet."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class CognitiveTestResultVisualizationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"detail": "Visualization feature not implemented yet."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class CognitiveSessionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        format_id = request.data.get("format_id")
        if not format_id:
            return Response({"error": "format_id is required"}, status=400)

        session = CognitiveSession.objects.create(user=request.user)

        for i in range(5):
            parameters = {
                "question": f"숫자 {randint(100, 999)}를 기억하세요",
                "difficulty": "easy",
                "index": i + 1,
            }
            problem = CognitiveProblem.objects.create(
                test_format_id=format_id,
                parameters=parameters,
                order=i + 1,
            )
            CognitiveSessionProblem.objects.create(session=session, problem=problem)

        serializer = CognitiveSessionWithProblemsSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CognitiveResultSRTAPIView(generics.CreateAPIView):
    serializer_class = CognitiveResultSRTSerializer
    permission_classes = [IsAuthenticated]


class CognitiveResultPatternAPIView(generics.CreateAPIView):
    serializer_class = CognitiveResultPatternSerializer
    permission_classes = [IsAuthenticated]


class CognitiveResultSymbolAPIView(generics.CreateAPIView):
    serializer_class = CognitiveResultSymbolSerializer
    permission_classes = [IsAuthenticated]