from collections import defaultdict
from random import randint

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
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
        today = timezone.localdate()  # ✅ 오늘 날짜 기준 (한국 시간)
        return CognitiveTestResult.objects.filter(
            user=self.request.user, timestamp__date=today
        ).order_by(
            "-timestamp"
        )  # 최신 순 정렬

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"has_data": False, "detail": "오늘의 인지 검사 결과가 없습니다."},
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

        return Response(
            {"session_id": session.id, "session": serializer.data},
            status=status.HTTP_201_CREATED,
        )


class CognitiveResultSRTAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        session_id = data.get("cognitiveSession") or data.get("cognitive_session")
        session = get_object_or_404(CognitiveSession, id=session_id, user=request.user)

        result = CognitiveResultSRT.objects.create(
            cognitive_session=session,
            score=data.get("score"),
            reaction_avg_ms=data.get("reactionAvgMs") or data.get("reaction_avg_ms"),
            reaction_list=",".join(map(str, data.get("reactionList", []))),
        )

        debug = try_create_test_result(request.user, session)

        return Response(
            {"detail": "SRT 저장 완료", "result_id": result.id, "debug": debug},
            status=status.HTTP_201_CREATED,
        )


class CognitiveResultSymbolAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        session_id = data.get("cognitiveSession") or data.get("cognitive_session")
        session = get_object_or_404(CognitiveSession, id=session_id, user=request.user)

        result = CognitiveResultSymbol.objects.create(
            cognitive_session=session,
            score=data.get("score"),
            symbol_correct=data.get("symbolCorrect") or data.get("symbol_correct"),
            symbol_accuracy=data.get("symbolAccuracy") or data.get("symbol_accuracy"),
        )

        debug = try_create_test_result(request.user, session)

        return Response(
            {"detail": "Symbol 저장 완료", "result_id": result.id, "debug": debug},
            status=status.HTTP_201_CREATED,
        )


class CognitiveResultPatternAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        session_id = data.get("cognitiveSession") or data.get("cognitive_session")
        session = get_object_or_404(CognitiveSession, id=session_id, user=request.user)

        result = CognitiveResultPattern.objects.create(
            cognitive_session=session,
            score=data.get("score"),
            pattern_correct=data.get("patternCorrect") or data.get("pattern_correct"),
            pattern_time_sec=data.get("patternTimeSec") or data.get("pattern_time_sec"),
        )

        debug = try_create_test_result(request.user, session)

        return Response(
            {"detail": "Pattern 저장 완료", "result_id": result.id, "debug": debug},
            status=status.HTTP_201_CREATED,
        )


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
                    "userId": user.id,
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
    if hasattr(session, "result"):
        return {"status": "이미 생성됨", "session_id": session.id}

    srt = CognitiveResultSRT.objects.filter(cognitive_session=session).first()
    sym = CognitiveResultSymbol.objects.filter(cognitive_session=session).first()
    pat = CognitiveResultPattern.objects.filter(cognitive_session=session).first()
    if not all([srt, sym, pat]):
        return {"status": "결과 미완성", "session_id": session.id}

    result = CognitiveTestResult.objects.create(
        user=user,
        test_format=session.test_format,
        cognitive_session=session,
        raw_scores={
            "srt": srt.score,
            "symbol": sym.score,
            "pattern": pat.score,
        },
        normalized_scores={},
        average_score=round((srt.score + sym.score + pat.score) / 3, 2),
        total_duration_sec=(
            int(srt.reaction_avg_ms * 10 // 1000)
            + sym.symbol_correct
            + int(pat.pattern_time_sec)
        ),
    )
    return {"status": "생성 완료", "result_id": result.id, "session_id": session.id}
