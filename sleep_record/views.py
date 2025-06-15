# 작성자: 한율
from datetime import datetime

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from sleep_record.serializers import SleepRecordSerializer
from sleep_record.services import (
    create_sleep_record,
    get_sleep_record,
    update_sleep_record,
)


class SleepRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = SleepRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        create_sleep_record(user=request.user, data=serializer.validated_data)

        return Response("message : 수면 기록이 작성 되었습니다.", status=201)

    def get(self, request: Request, id) -> Response:

        record = get_sleep_record(user=request.user, id=id)

        serializer = SleepRecordSerializer(record)
        return Response(serializer.data, status=200)

    def patch(self, request: Request, id) -> Response:

        serializer = SleepRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_sleep_record(user=request.user, data=serializer.validated_data, id=id)

        return Response("message : 수면 기록이 수정 되었습니다.", status=200)
