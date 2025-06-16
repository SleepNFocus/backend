from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import JobSurvey, UserStatus

from .serializers import (
    LogoutSerializer,
    MypageMainSerializer,
    MypageProfileSerializer,
    MypageRecordDaySerializer,
    MypageRecordMonthSerializer,
    MypageRecordWeekSerializer,
    OnboardingBasicSerializer,
    OnboardingJobSerializer,
    SocialLoginSerializer,
)
from .services import (
    SocialLoginService,
    get_mypage_main_data,
    get_record_day_list,
    get_record_month_list,
    get_record_week_list,
)
from .utils import add_token_to_blacklist, handle_social_login_error


# 소셜 로그인/자동 로그인
class SocialLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # serializer로 데이터 검사
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data["provider"]
        code = serializer.validated_data.get("code")
        access_token = serializer.validated_data.get("access_token")

        try:
            tokens, user = SocialLoginService.social_login(
                provider=provider, code=code, access_token=access_token
            )
        except Exception as e:
            # 함수로 에러 메세지 반환
            return handle_social_login_error(str(e))

        # 토큰/유저 정보 응답
        return Response(
            {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": {
                    "user_id": user.user_id,
                    "social_type": user.social_type,
                    "social_id": user.social_id,
                    "nickname": user.nickname,
                    "email": user.email,
                    "profile_img": user.profile_img,
                    "status": user.status,
                },
            },
            status=200,
        )


# 로그아웃(리프레시 토큰 무효화)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # serializer로 유효성 검사
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 검사 통과 시 리프레시 토큰 꺼냄
        refresh_token = serializer.validated_data["refresh"]
        # 리프레시 토큰을 블랙리스트에 저장함
        add_token_to_blacklist(refresh_token)

        return Response({"message": "정상적으로 로그아웃되었습니다."}, status=200)


# 회원 탈퇴
class UserWithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.status = UserStatus.WITHDRAWN
        user.save()
        return Response({"message": "계정이 삭제되었습니다."}, status=200)


# 온보딩 설문
# 기본 정보 저장
class OnboardingBasicView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OnboardingBasicSerializer(
            instance=request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(OnboardingBasicSerializer(user).data, status=200)


# 직업 설문 저장
class OnboardingJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OnboardingJobSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)


# 마이페이지 메인
class MypageMainView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = get_mypage_main_data(user)
        serializer = MypageMainSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


# 마이페이지 프로필 상세 조회 및 프로필 수정
class MypageProfileView(APIView):
    permission_classes = [IsAuthenticated]

    # 프로필 상세 조회
    def get(self, request):
        user = request.user
        # 최신 직업 설문 데이터를 조회하여 context로 전달
        latest_survey = (
            JobSurvey.objects.filter(user=user).order_by("-created_at").first()
        )
        serializer = MypageProfileSerializer(
            user, context={"request": request, "latest_job_survey": latest_survey}
        )
        return Response(serializer.data)

    # 프로필 수정
    def patch(self, request):
        user = request.user
        serializer = MypageProfileSerializer(
            user, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            # 저장 후 최신 직업 설문 데이터 다시 조회
            latest_survey = (
                JobSurvey.objects.filter(user=user).order_by("-created_at").first()
            )
            # context에 최신 설문 데이터 포함 후 다시 직렬화
            response_serializer = MypageProfileSerializer(
                user, context={"request": request, "latest_job_survey": latest_survey}
            )
            return Response(response_serializer.data)

        return Response(serializer.errors, status=400)


# 마이페이지 기록 조회 (리스트뷰-일,주,월)
class MypageRecordListView(APIView):
    permission_classes = [IsAuthenticated]

    # 각 기간별 처리 함수 및 시리얼라이저 연결
    PERIOD_MAP = {
        "day": (get_record_day_list, MypageRecordDaySerializer),
        "week": (get_record_week_list, MypageRecordWeekSerializer),
        "month": (get_record_month_list, MypageRecordMonthSerializer),
    }

    def get(self, request):
        # 조회 기간 파라미터
        period = request.GET.get("period")
        if period not in self.PERIOD_MAP:
            return Response(
                {"detail": "period는 day, week, month 중 하나입니다."}, status=400
            )

        # 각 기간에 맞는 함수 및 시리얼라이저를 선택
        get_func, serializer_class = self.PERIOD_MAP[period]

        # 기간별 기록 데이터 조회
        results = get_func(request.user)
        if not results:
            return Response({"detail": "해당 기간 기록이 없습니다."}, status=404)

        serializer = serializer_class(results, many=True)
        return Response({"results": serializer.data})
