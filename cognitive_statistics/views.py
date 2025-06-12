from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CognitiveTestFormat, CognitiveTestResult, CognitiveTestType
from .serializers import (
    CognitiveTestFormatSerializer,
    CognitiveTestResultSerializer,
    CognitiveTestTimeSerializer,
    CognitiveTestTypeSerializer,
)


# 메타 정보 조회: 유형 목록
class CognitiveTestTypeListAPIView(generics.ListAPIView):
    queryset = CognitiveTestType.objects.all()
    serializer_class = CognitiveTestTypeSerializer
    permission_classes = [IsAuthenticated]


# 메타 정보 조회: 형식(세부) 목록
class CognitiveTestFormatListAPIView(generics.ListAPIView):
    queryset = CognitiveTestFormat.objects.select_related("test_type").all()
    serializer_class = CognitiveTestFormatSerializer
    permission_classes = [IsAuthenticated]


# 테스트 소요 시간 저장
class CognitiveTestTimeSaveAPIView(generics.CreateAPIView):
    serializer_class = CognitiveTestTimeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# 권장 시간 안내(가이드)
class CognitiveTestTimeGuideAPIView(generics.ListAPIView):
    queryset = CognitiveTestFormat.objects.all()
    serializer_class = CognitiveTestFormatSerializer
    permission_classes = [IsAuthenticated]


# 기본 결과 조회(히스토리)
class CognitiveTestResultBasicAPIView(generics.ListAPIView):
    serializer_class = CognitiveTestResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CognitiveTestResult.objects.filter(user=self.request.user)


# 상관관계 분석 (REQ-017)
class CognitiveTestResultCorrelationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        # TODO: 수면 기록과 테스트 결과 간 상관계산 로직 구현
        return Response(
            {"detail": "Correlation feature not implemented yet."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


# 시각화 데이터 제공 (REQ-018)
class CognitiveTestResultVisualizationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        # TODO: 레이더 차트/시계열 차트용 데이터 구성 로직 구현
        return Response(
            {"detail": "Visualization feature not implemented yet."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
