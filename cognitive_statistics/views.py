# cognitive_statistics/views.py
from collections import defaultdict
from random import randint

from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cognitives.models import CognitiveProblem
from sleep_record.models import SleepRecord

from .models import (
    CognitiveResultPattern,
    CognitiveResultSRT,
    CognitiveResultSymbol,
    CognitiveSession,
    CognitiveSessionProblem,
    CognitiveTestFormat,
    CognitiveTestResult,
    CognitiveTestType,
)
from .serializers import (
    CognitiveResultPatternSerializer,
    CognitiveResultSRTSerializer,
    CognitiveResultSymbolSerializer,
    CognitiveSessionWithProblemsSerializer,
    CognitiveTestFormatSerializer,
    CognitiveTestResultDetailedSerializer,
    CognitiveTestTimeSerializer,
    CognitiveTestTypeSerializer,
)


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
    permission_classes = [IsAuthenticated]
    serializer_class = CognitiveTestResultDetailedSerializer

    def get_queryset(self):
        return CognitiveTestResult.objects.filter(user=self.request.user)


class CognitiveTestResultCorrelationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {"detail": "Correlation feature not implemented yet."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class CognitiveTestResultVisualizationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 가장 최근 테스트 결과 1개 가져오기
        latest_results = CognitiveTestResult.objects.filter(user=user).order_by(
            "-timestamp"
        )
        if not latest_results.exists():
            return Response({"detail": "결과 없음"}, status=404)

        radar = {}
        for result in latest_results:
            format_name = result.test_format.name.lower()
            if "srt" in format_name:
                radar["srt"] = result.average_score * 100
            elif "pattern" in format_name:
                radar["pattern_memory"] = result.average_score * 100
            elif "symbol" in format_name:
                radar["symbol_matching"] = result.average_score * 100
            if len(radar) == 3:
                break

        # 최근 7일 평균 점수 및 수면 시간 추이 계산
        recent_results = CognitiveTestResult.objects.filter(user=user).order_by(
            "-timestamp"
        )[:7]
        dates = []
        avg_scores = []
        sleep_hours = []

        for result in recent_results:
            date_str = result.timestamp.strftime("%Y-%m-%d")
            dates.append(date_str)
            avg_scores.append(round(result.average_score * 100, 2))

            sleep_record = SleepRecord.objects.filter(
                user=user, date=result.timestamp.date()
            ).first()
            sleep_hours.append(sleep_record.sleep_duration if sleep_record else 0)

        calendar = {
            result.timestamp.strftime("%Y-%m-%d"): {
                "score": round(result.average_score * 100, 2),
                "sleep": (
                    sleep_record.sleep_duration
                    if (
                        sleep_record := SleepRecord.objects.filter(
                            user=user, date=result.timestamp.date()
                        ).first()
                    )
                    else 0
                ),
            }
            for result in recent_results
        }

        return Response(
            {
                "radar_chart": radar,
                "trend_7d": {
                    "dates": dates[::-1],
                    "average_scores": avg_scores[::-1],
                    "sleep_hours": sleep_hours[::-1],
                },
                "calendar": calendar,
            },
            status=status.HTTP_200_OK,
        )


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
