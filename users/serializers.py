from rest_framework import serializers

from users.models import Gender, JobSurvey, MBTIType, User

from .utils import normalize_mbti


# 소셜 로그인(회원가입)
class SocialLoginSerializer(serializers.Serializer):
    provider: str = serializers.ChoiceField(
        choices=[("kakao", "KAKAO"), ("google", "GOOGLE")]
    )
    code: str = serializers.CharField(required=False, allow_blank=True)
    access_token: str = serializers.CharField(required=False, allow_blank=True)

    # code or access_token 중 하나만 필수

    def validate(self, data: dict) -> dict:
        code = data.get("code")
        access_token = data.get("access_token")

        if not code and not access_token:
            raise serializers.ValidationError(
                "code 또는 access_token 중 하나는 필수입니다."
            )
        if code and access_token:
            raise serializers.ValidationError(
                "code, access_token 중 하나만 입력해주세요."
            )
        return data


# 로그아웃(리프레시 토큰 무효화)
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        if not value:
            raise serializers.ValidationError("리프레시 토큰은 필수입니다.")
        return value


# 온보딩 설문
# 기본 정보 설문
class OnboardingBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["gender", "birth_year", "mbti"]

    # 기본 설문 정보 저장 시 db에 업데이트
    def update(self, instance, validated_data):
        # gender 선택안함 선택 시 null 처리
        gender = validated_data.get("gender")
        if gender == "선택안함":
            validated_data["gender"] = None

        # mbti 선택안함 선택 시 null 처리
        validated_data["mbti"] = normalize_mbti(validated_data.get("mbti"))
        # 필드 값을 유저 인스턴스에 저장
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# 직업 설문
class OnboardingJobSerializer(serializers.ModelSerializer):
    cognitive_type_label = serializers.SerializerMethodField()
    work_time_pattern_label = serializers.SerializerMethodField()

    class Meta:
        model = JobSurvey
        fields = [
            "cognitive_type",
            "cognitive_type_label",
            "work_time_pattern",
            "work_time_pattern_label",
        ]

    # cognitive_type의 라벨을 같이 불러옴
    def get_cognitive_type_label(self, obj):
        return obj.get_cognitive_type_display()

    # work_time_pattern의 라벨을 같이 불러옴
    def get_work_time_pattern_label(self, obj):
        return obj.get_work_time_pattern_display()

    # 유저 정보와 설문 데이터로 설문 결과를 새로 저장
    def create(self, validated_data):
        user = self.context.get("request").user
        return JobSurvey.objects.create(user=user, **validated_data)


# 마이페이지 메인
class MypageMainSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    profile_img = serializers.CharField(allow_null=True, required=False)
    joined_at = serializers.DateTimeField()
    tracking_days = serializers.IntegerField()
    total_sleep_hours = serializers.FloatField()
    average_sleep_score = serializers.FloatField()
    average_cognitive_score = serializers.FloatField()


# 마이페이지 프로필 상세 조회 및 프로필 수정
class MypageProfileSerializer(serializers.ModelSerializer):
    # User 필드
    gender = serializers.ChoiceField(choices=Gender, allow_null=True, required=True)
    mbti = serializers.ChoiceField(choices=MBTIType, allow_null=True, required=True)
    profile_img = serializers.ImageField(
        required=False, allow_null=True
    )  # 파일 업로드용

    # JobSurvey 입력용(쓰기) 필드
    cognitive_type = serializers.ChoiceField(
        choices=[c[0] for c in JobSurvey._meta.get_field("cognitive_type").choices],
        required=False,
        write_only=True,
    )
    work_time_pattern = serializers.ChoiceField(
        choices=[c[0] for c in JobSurvey._meta.get_field("work_time_pattern").choices],
        required=False,
        write_only=True,
    )

    # JobSurvey 응답용 필드 (항상 최신 설문 값 반환)
    cognitive_type_label = serializers.SerializerMethodField()
    work_time_pattern_label = serializers.SerializerMethodField()
    # 타입도 응답용으로 뽑아줌
    cognitive_type_out = serializers.SerializerMethodField()
    work_time_pattern_out = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "nickname",
            "profile_img",
            "gender",
            "birth_year",
            "mbti",
            "cognitive_type",  # 요청: patch로 보내는 용도(write_only)
            "work_time_pattern",
            "cognitive_type_out",  # 응답: 항상 최신 설문값 반환(read_only)
            "cognitive_type_label",
            "work_time_pattern_out",
            "work_time_pattern_label",
            "email",
        ]
        # 수정 불가 필드
        read_only_fields = [
            "email",
            "cognitive_type_out",
            "cognitive_type_label",
            "work_time_pattern_out",
            "work_time_pattern_label",
        ]

    def get_latest_job_survey(self, user):
        # 유저의 가장 최근 직업 설문 값 반환
        return (
            self.context.get("latest_job_survey")
            or JobSurvey.objects.filter(user=user).order_by("-created_at").first()
        )

    def get_cognitive_type_label(self, obj):
        # 최신 직업 설문 값의 라벨 반환
        job_survey = self.get_latest_job_survey(obj)
        return job_survey.get_cognitive_type_display() if job_survey else None

    def get_work_time_pattern_label(self, obj):
        # 최신 직업 설문 값의 라벨 반환
        job_survey = self.get_latest_job_survey(obj)
        return job_survey.get_work_time_pattern_display() if job_survey else None

    def get_cognitive_type_out(self, obj):
        # 최신 직업 설문 값 반환 (응답용)
        job_survey = self.get_latest_job_survey(obj)
        return job_survey.cognitive_type if job_survey else None

    def get_work_time_pattern_out(self, obj):
        # 최신 직업 설문 값 반환 (응답용)
        job_survey = self.get_latest_job_survey(obj)
        return job_survey.work_time_pattern if job_survey else None

    # User & JobSurvey 필드 수정
    def update(self, instance, validated_data):
        # gender '선택안함' 처리
        gender = validated_data.get("gender")
        if gender == "선택안함":
            validated_data["gender"] = None

        # mbti '선택안함' 처리
        mbti = validated_data.get("mbti")
        if mbti == "선택안함":
            validated_data["mbti"] = None

        # 프로필 이미지 새로 업로드시 항상 같은 이름(profile/{user_id}.jpg)으로 저장 (덮어쓰기))
        profile_img = validated_data.get("profile_img", None)
        if profile_img:
            # 기존 파일 삭제
            if instance.profile_img:
                instance.profile_img.delete(save=False)
            # 같은 이름으로 저장
            file_name = f"profile/{instance.user_id}.jpg"
            instance.profile_img.save(file_name, profile_img)
            # validated_data에서 profile_img 키 제거 (이미 직접 할당함)
            validated_data.pop("profile_img")

        # 입력된 직업 설문 분리
        cognitive_type = validated_data.pop("cognitive_type", None)
        work_time_pattern = validated_data.pop("work_time_pattern", None)

        # User 필드 저장
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 직업 설문 값이 둘 중 하나라도 있으면 이전 값으로 채워서 JobSurvey 인스턴스 새로 생성
        if cognitive_type is not None or work_time_pattern is not None:
            latest = (
                JobSurvey.objects.filter(user=instance).order_by("-created_at").first()
            )
            # 이전 값으로 채우기
            if latest:
                if cognitive_type is None:
                    cognitive_type = latest.cognitive_type
                if work_time_pattern is None:
                    work_time_pattern = latest.work_time_pattern
            latest_survey = JobSurvey.objects.create(
                user=instance,
                cognitive_type=cognitive_type,
                work_time_pattern=work_time_pattern,
            )
            # context에 최신 데이터 반영
            self.context["latest_job_survey"] = latest_survey

        return instance


# 마이페이지 기록 조회 (리스트뷰-일별)
class MypageRecordDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    sleep_hour = serializers.FloatField()
    sleep_score = serializers.FloatField()
    cognitive_score = serializers.FloatField()


# 마이페이지 기록 조회 (리스트뷰-주별)
class MypageRecordWeekSerializer(serializers.Serializer):
    week = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_sleep_hours = serializers.FloatField()
    average_sleep_score = serializers.FloatField()
    average_cognitive_score = serializers.FloatField()


# 마이페이지 기록 조회 (리스트뷰-월별)
class MypageRecordMonthSerializer(serializers.Serializer):
    month = serializers.CharField()
    total_sleep_hours = serializers.FloatField()
    average_sleep_score = serializers.FloatField()
    average_cognitive_score = serializers.FloatField()


# 마이페이지 선택 날짜 기록 상세 조회
# Cognitive test 상세
class MypageRecordDetailCognitiveSerializer(serializers.Serializer):
    srt_score = serializers.FloatField()
    srt_time_ms = serializers.IntegerField()
    symbol_score = serializers.FloatField()
    symbol_count = serializers.IntegerField()
    symbol_accuracy = serializers.IntegerField()
    pattern_score = serializers.FloatField()
    pattern_count = serializers.IntegerField()
    pattern_time_ms = serializers.FloatField()


# detail 전체
class MypageRecordDetailSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_sleep_hours = serializers.FloatField()
    sleep_score = serializers.FloatField()
    cognitive_test = MypageRecordDetailCognitiveSerializer()


# graph 블록
class MypageRecordGraphSerializer(serializers.Serializer):
    dates = serializers.ListField(child=serializers.DateField())
    sleep_hour_list = serializers.ListField(child=serializers.FloatField())
    sleep_score_list = serializers.ListField(child=serializers.FloatField())
    cognitive_score_list = serializers.ListField(child=serializers.FloatField())
    selected_date = serializers.DateField()


# 최상위 응답
class MypageRecordDetailResponseSerializer(serializers.Serializer):
    graph = MypageRecordGraphSerializer()
    detail = MypageRecordDetailSerializer()
