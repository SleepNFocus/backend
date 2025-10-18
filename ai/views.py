from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.services import generate_ai_recommendation


class AIRecommendContentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date = request.query_params.get("date")

        if not date:
            return Response({"detail": "날짜를 입력해주세요 (YYYY-MM-DD)"}, status=400)

        result = generate_ai_recommendation(request.user, date)

        if "error" in result:
            return Response({"detail": result["error"]}, status=404)

        # result["recommendation"]가 문자열이라면
        return Response({"recommendation": result["recommendation"]}, status=200)
