from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from cognitive_statistics.models import CognitiveTestFormat, CognitiveTestResult
from .models import CognitiveProblem, CognitiveResponse
from .serializers import (
    CognitiveProblemSerializer,
    TestPlayListSerializer,
    TestSubmitSerializer
)

# 1) 플레이 가능한 테스트 포맷 목록 조회
class TestPlayListAPIView(generics.ListAPIView):
    queryset = CognitiveTestFormat.objects.all()
    serializer_class = TestPlayListSerializer
    permission_classes = [permissions.IsAuthenticated]


# 2) 특정 테스트 형식 문제 불러오기
class TestPlayAPIView(generics.ListAPIView):
    serializer_class = CognitiveProblemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        fmt = get_object_or_404(
            CognitiveTestFormat,
            name=self.kwargs['test_type']
        )
        return CognitiveProblem.objects.filter(test_format=fmt)


# 3) 응답 제출 및 결과 저장
class TestSubmitAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, test_type):
        serializer = TestSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fmt = get_object_or_404(
            CognitiveTestFormat,
            name=test_type
        )
        answers = serializer.validated_data['answers']

        raw_scores = {}
        total_time = 0

        # 각 응답 저장
        for ans in answers:
            prob = get_object_or_404(CognitiveProblem, pk=ans['problem_id'])
            resp = CognitiveResponse.objects.create(
                user=request.user,
                problem=prob,
                submitted_answer=ans['answer'],
                response_time_ms=ans['response_time_ms']
            )
            raw_scores[str(prob.pk)] = resp.response_time_ms
            total_time += resp.response_time_ms

        # TODO: 정규화 로직 적용 필요
        normalized_scores = raw_scores
        average_score = sum(normalized_scores.values()) / len(normalized_scores)

        # 종합 결과 저장 (cognitive_statistics 앱)
        CognitiveTestResult.objects.create(
            user=request.user,
            raw_scores=raw_scores,
            normalized_scores=normalized_scores,
            average_score=average_score,
            total_duration_sec=total_time // 1000
        )

        return Response({'detail': 'Submitted'}, status=status.HTTP_201_CREATED)