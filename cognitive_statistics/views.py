from collections import defaultdict
from datetime import datetime
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
        all_results = self.get_queryset()

        if not all_results.exists():
            return Response(
                {"has_data": False, "detail": "인지 검사 결과가 없습니다."},
                status=status.HTTP_200_OK,
            )

        # 최신 하나 분리
        latest_result = all_results.first()

        # 오늘 날짜 (Y-m-d 기준)
        today = datetime.now().date()
        today_others = all_results.exclude(id=latest_result.id).filter(
            timestamp__date=today
        )

        serializer = self.get_serializer(
            [latest_result] + list(today_others), many=True
        )
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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        session_id = data.get("cognitiveSession") or data.get("cognitive_session")
        score = data.get("score")
        avg_ms = data.get("reactionAvgMs") or data.get("reaction_avg_ms")
        reaction_raw = data.get("reactionList") or data.get("reaction_list") or []
        reaction_list_str = (
            ",".join(map(str, reaction_raw))
            if isinstance(reaction_raw, list)
            else reaction_raw
        )

        try:
            session = CognitiveSession.objects.get(id=session_id, user=request.user)
        except CognitiveSession.DoesNotExist:
            return Response({"error": "세션을 찾을 수 없습니다."}, status=404)

        result = CognitiveResultSRT.objects.create(
            cognitive_session=session,
            score=score,
            reaction_avg_ms=avg_ms,
            reaction_list=reaction_list_str,
        )

        result_info = try_create_test_result(request.user, session)

        return Response(
            {
                "detail": "SRT 저장 완료",
                "result_id": result.id,
                "test_result_debug": result_info,
            },
            status=201,
        )


class CognitiveResultPatternAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        session_id = data.get("cognitiveSession") or data.get("cognitive_session")

        try:
            session = CognitiveSession.objects.get(id=session_id, user=request.user)
        except CognitiveSession.DoesNotExist:
            return Response({"error": "세션을 찾을 수 없습니다."}, status=404)

        result = CognitiveResultPattern.objects.create(
            cognitive_session=session,
            score=data.get("score"),
            pattern_correct=data.get("patternCorrect") or data.get("pattern_correct"),
            pattern_time_sec=data.get("patternTimeSec") or data.get("pattern_time_sec"),
        )

        result_info = try_create_test_result(request.user, session)

        return Response(
            {
                "detail": "Pattern 저장 완료",
                "result_id": result.id,
                "test_result_debug": result_info,
            },
            status=201,
        )


class CognitiveResultSymbolAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        session_id = data.get("cognitiveSession") or data.get("cognitive_session")

        try:
            session = CognitiveSession.objects.get(id=session_id, user=request.user)
        except CognitiveSession.DoesNotExist:
            return Response({"error": "세션을 찾을 수 없습니다."}, status=404)

        result = CognitiveResultSymbol.objects.create(
            cognitive_session=session,
            score=data.get("score"),
            symbol_correct=data.get("symbolCorrect") or data.get("symbol_correct"),
            symbol_accuracy=data.get("symbolAccuracy") or data.get("symbol_accuracy"),
        )

        result_info = try_create_test_result(request.user, session)

        return Response(
            {
                "detail": "Symbol 저장 완료",
                "result_id": result.id,
                "test_result_debug": result_info,
            },
            status=201,
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
    srt = CognitiveResultSRT.objects.filter(cognitive_session=session).first()
    symbol = CognitiveResultSymbol.objects.filter(cognitive_session=session).first()
    pattern = CognitiveResultPattern.objects.filter(cognitive_session=session).first()

    result_info = {
        "srt_exists": bool(srt),
        "symbol_exists": bool(symbol),
        "pattern_exists": bool(pattern),
        "has_test_format": bool(session.test_format),
        "already_created": CognitiveTestResult.objects.filter(
            user=user, test_format=session.test_format
        ).exists(),
    }

    if not all(
        [
            result_info["srt_exists"],
            result_info["symbol_exists"],
            result_info["pattern_exists"],
        ]
    ):
        result_info["status"] = "조건 부족으로 CognitiveTestResult 생성 안됨"
        return result_info

    if not result_info["has_test_format"]:
        result_info["status"] = "test_format 없음"
        return result_info

    if result_info["already_created"]:
        result_info["status"] = "이미 생성됨"
        return result_info

    result = CognitiveTestResult.objects.create(
        user=user,
        test_format=session.test_format,
        raw_scores={
            "srt": srt.score,
            "symbol": symbol.score,
            "pattern": pattern.score,
        },
        normalized_scores={},
        average_score=round((srt.score + symbol.score + pattern.score) / 3, 2),
        total_duration_sec=int(srt.reaction_avg_ms * 10 / 1000)
        + symbol.symbol_correct
        + int(pattern.pattern_time_sec),
    )

    result_info["status"] = "✅ CognitiveTestResult 생성 완료"
    result_info["created_id"] = result.id
    return result_info
