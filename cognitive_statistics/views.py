# cognitive_statistics/views.py
from random import randint

from django.db.models import Avg, Sum
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


class CognitiveResultSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        sessions = CognitiveSession.objects.filter(user=user)

        srt_qs = CognitiveResultSRT.objects.filter(cognitive_session__in=sessions)
        symbol_qs = CognitiveResultSymbol.objects.filter(cognitive_session__in=sessions)
        pattern_qs = CognitiveResultPattern.objects.filter(
            cognitive_session__in=sessions
        )

        srt_data = {
            "avg_ms": round(
                srt_qs.aggregate(avg=Avg("reaction_avg_ms"))["avg"] or 0, 2
            ),
            "total_duration_sec": round(
                srt_qs.count()
                * (srt_qs.aggregate(avg=Avg("reaction_avg_ms"))["avg"] or 0)
                / 1000,
                2,
            ),
            "average_score": round(srt_qs.aggregate(avg=Avg("score"))["avg"] or 0, 2),
        }

        symbol_data = {
            "correct": symbol_qs.aggregate(total=Sum("symbol_correct"))["total"] or 0,
            "avg_ms": round(
                symbol_qs.aggregate(avg=Avg("symbol_accuracy"))["avg"] or 0 * 1000, 2
            ),
            "symbol_accuracy": round(
                symbol_qs.aggregate(avg=Avg("symbol_accuracy"))["avg"] or 0, 2
            ),
            "total_duration_sec": symbol_qs.aggregate(total=Sum("symbol_correct"))[
                "total"
            ]
            or 0,
            "average_score": round(
                symbol_qs.aggregate(avg=Avg("score"))["avg"] or 0, 2
            ),
        }

        pattern_data = {
            "correct": pattern_qs.aggregate(total=Sum("pattern_correct"))["total"] or 0,
            "total_duration_sec": round(
                pattern_qs.aggregate(total=Sum("pattern_time_sec"))["total"] or 0, 2
            ),
            "average_score": round(
                pattern_qs.aggregate(avg=Avg("score"))["avg"] or 0, 2
            ),
        }

        normalized_scores = {
            "srt": srt_data["average_score"],
            "symbol": symbol_data["average_score"],
            "pattern": pattern_data["average_score"],
        }

        average_score = round(sum(normalized_scores.values()) / 3, 2)
        total_duration_sec = (
            srt_data["total_duration_sec"]
            + symbol_data["total_duration_sec"]
            + pattern_data["total_duration_sec"]
        )

        return Response(
            {
                "raw_scores": {
                    "srt": srt_data,
                    "symbol": symbol_data,
                    "pattern": pattern_data,
                },
                "normalized_scores": normalized_scores,
                "average_score": average_score,
                "total_duration_sec": total_duration_sec,
            }
        )
