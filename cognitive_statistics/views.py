from collections import defaultdict
from random import randint

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cognitives.models import CognitiveProblem

from .models import (
    CognitiveResultPattern,
    CognitiveResultSRT,
    CognitiveResultSymbol,
    CognitiveSession,
    CognitiveSessionProblem,
    CognitiveTestFormat,
    CognitiveTestResult,
)
from .serializers import (
    CognitiveSessionWithProblemsSerializer,
    CognitiveTestResultDetailedSerializer,
)


class CognitiveTestResultBasicAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CognitiveTestResultDetailedSerializer

    def get_queryset(self):
        return CognitiveTestResult.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"has_data": False, "detail": "인지 검사 결과가 없습니다."},
                status=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response({"has_data": True, "results": serializer.data})


class CognitiveSessionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        format_id = request.data.get("format_id")
        if not format_id:
            return Response({"error": "format_id is required"}, status=400)

        try:
            test_format = CognitiveTestFormat.objects.get(id=format_id)
        except CognitiveTestFormat.DoesNotExist:
            return Response({"error": "존재하지 않는 format_id"}, status=400)
        session = CognitiveSession.objects.create(
            user=request.user, test_format=test_format
        )

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


class CognitiveResultSRTAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        session_id = data.get("cognitiveSession")

        try:
            session = CognitiveSession.objects.get(id=session_id, user=request.user)
        except CognitiveSession.DoesNotExist:
            return Response({"error": "세션을 찾을 수 없습니다."}, status=404)

        result = CognitiveResultSRT.objects.create(
            cognitive_session=session,
            score=data.get("score"),
            reaction_avg_ms=data.get("reactionAvgMs"),
            reaction_list=",".join(map(str, data.get("reactionList", []))),
        )
        try_create_test_result(request.user, session)
        return Response({"detail": "SRT 저장 완료", "id": result.id}, status=201)


class CognitiveResultPatternAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        session_id = data.get("cognitiveSession")

        try:
            session = CognitiveSession.objects.get(id=session_id, user=request.user)
        except CognitiveSession.DoesNotExist:
            return Response({"error": "세션을 찾을 수 없습니다."}, status=404)

        result = CognitiveResultPattern.objects.create(
            cognitive_session=session,
            score=data.get("score"),
            pattern_correct=data.get("patternCorrect"),
            pattern_time_sec=data.get("patternTimeSec"),
        )
        try_create_test_result(request.user, session)
        return Response({"detail": "Pattern 저장 완료", "id": result.id}, status=201)


class CognitiveResultSymbolAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        session_id = data.get("cognitiveSession")

        try:
            session = CognitiveSession.objects.get(id=session_id, user=request.user)
        except CognitiveSession.DoesNotExist:
            return Response({"error": "세션을 찾을 수 없습니다."}, status=404)

        result = CognitiveResultSymbol.objects.create(
            cognitive_session=session,
            score=data.get("score"),
            symbol_correct=data.get("symbolCorrect"),
            symbol_accuracy=data.get("symbolAccuracy"),
        )
        try_create_test_result(request.user, session)
        return Response({"detail": "Symbol 저장 완료", "id": result.id}, status=201)


class CognitiveResultDailySummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        sessions = CognitiveSession.objects.filter(user=user)

        daily_summary = defaultdict(
            lambda: {
                "srt": {"scores": [], "avg_ms": []},
                "symbol": {"scores": [], "correct": 0, "avg_ms": [], "accuracy": []},
                "pattern": {"scores": [], "correct": 0},
            }
        )

        for session in sessions:
            date_str = session.started_at.date().isoformat()

            srt = CognitiveResultSRT.objects.filter(cognitive_session=session).first()
            if srt:
                daily_summary[date_str]["srt"]["scores"].append(srt.score)
                daily_summary[date_str]["srt"]["avg_ms"].append(srt.reaction_avg_ms)

            symbol = CognitiveResultSymbol.objects.filter(
                cognitive_session=session
            ).first()
            if symbol:
                daily_summary[date_str]["symbol"]["scores"].append(symbol.score)
                daily_summary[date_str]["symbol"]["correct"] += (
                    symbol.symbol_correct or 0
                )
                daily_summary[date_str]["symbol"]["avg_ms"].append(
                    symbol.symbol_accuracy * 1000
                )  # 예시
                daily_summary[date_str]["symbol"]["accuracy"].append(
                    symbol.symbol_accuracy
                )

            pattern = CognitiveResultPattern.objects.filter(
                cognitive_session=session
            ).first()
            if pattern:
                daily_summary[date_str]["pattern"]["scores"].append(pattern.score)
                daily_summary[date_str]["pattern"]["correct"] += (
                    pattern.pattern_correct or 0
                )

        result = []
        for date, data in sorted(daily_summary.items()):
            srt_scores = data["srt"]["scores"]
            srt_avg_ms = data["srt"]["avg_ms"]

            symbol_scores = data["symbol"]["scores"]
            symbol_avg_ms = data["symbol"]["avg_ms"]
            symbol_accs = data["symbol"]["accuracy"]

            pattern_scores = data["pattern"]["scores"]

            srt_score = round(sum(srt_scores) / len(srt_scores), 2) if srt_scores else 0
            symbol_score = (
                round(sum(symbol_scores) / len(symbol_scores), 2)
                if symbol_scores
                else 0
            )
            pattern_score = (
                round(sum(pattern_scores) / len(pattern_scores), 2)
                if pattern_scores
                else 0
            )

            avg_score = round((srt_score + symbol_score + pattern_score) / 3, 2)

            result.append(
                {
                    "date": date,
                    "userId": user.user_id,
                    "average_score": avg_score,
                    "raw_scores": {
                        "srt": {
                            "average_score": srt_score,
                            "avg_ms": (
                                round(sum(srt_avg_ms) / len(srt_avg_ms), 2)
                                if srt_avg_ms
                                else 0
                            ),
                        },
                        "symbol": {
                            "average_score": symbol_score,
                            "correct": data["symbol"]["correct"],
                            "avg_ms": (
                                round(sum(symbol_avg_ms) / len(symbol_avg_ms), 2)
                                if symbol_avg_ms
                                else 0
                            ),
                            "symbol_accuracy": (
                                round(sum(symbol_accs) / len(symbol_accs), 2)
                                if symbol_accs
                                else 0
                            ),
                        },
                        "pattern": {
                            "average_score": pattern_score,
                            "correct": data["pattern"]["correct"],
                        },
                    },
                }
            )

        return Response(result)


def try_create_test_result(user, session):
    srt = CognitiveResultSRT.objects.filter(cognitive_session=session).first()
    symbol = CognitiveResultSymbol.objects.filter(cognitive_session=session).first()
    pattern = CognitiveResultPattern.objects.filter(cognitive_session=session).first()

    if not (srt and symbol and pattern):
        return  # 아직 하나라도 없음

    if CognitiveTestResult.objects.filter(
        user=user, test_format=session.test_format
    ).exists():
        return  # 이미 생성됨

    avg_score = round((srt.score + symbol.score + pattern.score) / 3, 2)
    duration = (
        int(srt.reaction_avg_ms * 10 / 1000)
        + int(symbol.symbol_correct)
        + int(pattern.pattern_time_sec)
    )

    CognitiveTestResult.objects.create(
        user=user,
        test_format=session.test_format,
        raw_scores={
            "srt": srt.score,
            "symbol": symbol.score,
            "pattern": pattern.score,
        },
        normalized_scores={},
        average_score=avg_score,
        total_duration_sec=duration,
    )
