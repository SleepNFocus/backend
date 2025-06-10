from urllib.request import Request

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sleep_record import services
from sleep_record.serializers import SleepRecordCreateSerializer
from users.models import User


class SleepRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = SleepRecordCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.create_sleep_record(user=request.user, data=serializer.validated_data)

        return Response("message : 수면 기록이 작성 되었습니다.", status=201)
