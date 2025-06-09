from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class TestPlayListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response("REQ-PLAY-LIST")


class TestPlayAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, test_type):
        return Response(f"REQ-PLAY-{test_type.upper()}")


class TestSubmitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, test_type):
        return Response(f"REQ-SUBMIT-{test_type.upper()}")
