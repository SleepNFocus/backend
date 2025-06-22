import logging
from datetime import datetime

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from sleep_record.serializers import SleepRecordSerializer
from sleep_record.services import (
    create_sleep_record,
    get_sleep_record,
    sleep_record_exists,
    update_sleep_record,
)

logger = logging.getLogger(__name__)


class SleepRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = SleepRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        create_sleep_record(user=request.user, data=serializer.validated_data)

        return Response("message : 수면 기록이 작성 되었습니다.", status=201)

    def get(self, request: Request) -> Response:
        date_str = request.query_params.get("date")

        if not date_str:
            return Response({"detail": "date는 필수입니다."}, status=400)

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "날짜 형식은 YYYY-MM-DD여야 합니다."}, status=400
            )

        record = get_sleep_record(user=request.user, date=date)

        if record is None:
            logger.info(
                "❗수면 기록 없음: user=%s, date=%s", request.user.user_id, date
            )
            return Response(None, status=200)

        serializer = SleepRecordSerializer(record)
        return Response(serializer.data, status=200)

    def patch(self, request: Request) -> Response:
        date = request.query_params.get("date")

        serializer = SleepRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not date:
            return Response({"detail": "date는 필수입니다."}, status=400)

        try:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "날짜 형식은 YYYY-MM-DD여야 합니다."}, status=400
            )

        update_sleep_record(
            user=request.user, data=serializer.validated_data, date=date
        )

        return Response("message : 수면 기록이 수정 되었습니다.", status=200)


class SleepRecordExistsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        date = request.query_params.get("date")

        if not date:
            return Response({"detail": "date는 필수입니다."}, status=400)

        try:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "날짜 형식은 YYYY-MM-DD여야 합니다."}, status=400
            )

        exists = sleep_record_exists(user=request.user, date=date)

        return Response({"exists": exists}, status=200)
