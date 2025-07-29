from datetime import datetime

import google.generativeai as genai
from django.conf import settings
from django.utils.timezone import make_aware

from cognitive_statistics.models import (
    CognitiveResultPattern,
    CognitiveResultSRT,
    CognitiveResultSymbol,
    CognitiveSession,
)
from sleep_record.models import SleepRecord


def get_sleep_and_cognitive_data(user, date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    sleep = SleepRecord.objects.filter(user=user, date=date).first()
    if not sleep:
        return None, None, "수면 기록이 없습니다."

    start_of_day = make_aware(datetime.combine(date, datetime.min.time()))
    end_of_day = make_aware(datetime.combine(date, datetime.max.time()))

    session = (
        CognitiveSession.objects.filter(
            user=user, started_at__range=(start_of_day, end_of_day)
        )
        .order_by("started_at")
        .first()
    )

    test_scores = {}
    if session:
        if srt := CognitiveResultSRT.objects.filter(cognitive_session=session).first():
            test_scores["srt"] = {"score": srt.score}
        if pattern := CognitiveResultPattern.objects.filter(
            cognitive_session=session
        ).first():
            test_scores["pattern"] = {"score": pattern.score}
        if symbol := CognitiveResultSymbol.objects.filter(
            cognitive_session=session
        ).first():
            test_scores["symbol"] = {"score": symbol.score}

    return sleep, test_scores, None


def generate_sleep_ai_prompt(sleep_data, test_scores, date):
    return f"""
너는 건강 전문 AI 추천 시스템이야.
다음은 {date}의 수면 기록과 인지 테스트 결과야.
수면 점수와 인지 점수가 모두 낮거나 일부 낮을 경우, 수면 질을 높이고 인지 수행 능력을 개선할 수 있는 팁이나 행동을 추천해줘.
추천은 3개 이하로 해줘. 간단한 이유도 함께 설명해줘.

[수면 기록]
- 수면 점수: {sleep_data['score']}/100
- 수면 시간: {sleep_data['sleep_duration']}분
- 주관적 수면 질: {sleep_data['subjective_quality']}/5
- 잠들기까지 걸린 시간: {sleep_data['sleep_latency']}분
- 자주 깬 횟수: {sleep_data['wake_count']}번
- 수면 방해 요인: {', '.join(sleep_data.get('disturb_factors', [])) or '없음'}

[인지 테스트 결과]
- 단순 반응 시간 점수 (SRT): {test_scores.get('srt', {}).get('score', '미실시')}
- 패턴 기억 점수: {test_scores.get('pattern', {}).get('score', '미실시')}
- 기호 매칭 점수: {test_scores.get('symbol', {}).get('score', '미실시')}

[형식]
1. 추천 항목 제목
   - 설명
"""


# views에서 실제로 호출하는 api
def generate_ai_recommendation(user, date_str):
    sleep, test_scores, error = get_sleep_and_cognitive_data(user, date_str)
    if error:
        return {"error": error}

    prompt = generate_sleep_ai_prompt(
        sleep_data={
            "score": sleep.score,
            "sleep_duration": sleep.sleep_duration,
            "subjective_quality": sleep.subjective_quality,
            "sleep_latency": sleep.sleep_latency,
            "wake_count": sleep.wake_count,
            "disturb_factors": sleep.disturb_factors,
        },
        test_scores=test_scores,
        date=str(sleep.date),
    )

    try:
        genai.configure(api_key=settings.GOOGLE_GENAI_API_KEY)
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
        response = model.generate_content(prompt)
        return {"recommendation": response.text}

    except GoogleAPIError as e:
        logger.error(f"[AI] Google Gemini API Error: {e}")
        return {"error": "AI 추천 생성에 실패했습니다. 잠시 후 다시 시도해주세요."}

    except Exception as e:
        logger.exception(f"[AI] 예기치 못한 오류: {e}")
        return {"error": "서버 오류로 AI 추천을 가져오지 못했습니다."}
