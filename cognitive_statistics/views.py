from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class CognitiveTestTypeListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response("REQ-011")


class CognitiveTestFormatListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response("REQ-012")


class CognitiveTestTimeSaveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        return Response("REQ-014")


class CognitiveTestTimeGuideAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response("REQ-015")


class CognitiveTestResultBasicAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response("REQ-016")


class CognitiveTestResultCorrelationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response("REQ-017")


class CognitiveTestResultVisualizationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response("REQ-018")
