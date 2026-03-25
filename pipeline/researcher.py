"""Step 4: Researcher — Gemini Pro + Google Search로 팩트 리서치"""

import json

from google import genai

from .config import GEMINI_API_KEY, MODEL_PRO, load_prompt


def research(plan: dict) -> dict:
    """기획안에 필요한 팩트/통계 리서치"""
    system_prompt = load_prompt("researcher")

    # 기획안에서 리서치 필요 항목 추출
    research_items = []
    for slide in plan.get("slides", []):
        needed = slide.get("research_needed", "")
        questions = slide.get("research_questions", [])
        if needed:
            research_items.append(f"- Slide {slide['slide_index']}: {needed}")
        for q in questions:
            research_items.append(f"  - 질문: {q}")

    user_message = f"""다음 카드뉴스 기획안에 필요한 데이터를 리서치해주세요:

앵글: {plan.get('angle', '')}
내러티브: {plan.get('narrative_arc', '')}

리서치 필요 항목:
{chr(10).join(research_items)}

Google Search를 사용해서 최신 정보를 찾아주세요."""

    print("[Researcher] Gemini Pro + Google Search로 리서치 중...")

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=MODEL_PRO,
        contents=[
            {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_message}]}
        ],
        config={
            "temperature": 0.4,
            "response_mime_type": "application/json",
            "tools": [{"google_search": {}}],
        },
    )

    # JSON 응답 파싱 시도
    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        # Google Search 결과가 포함된 경우 텍스트에서 JSON 추출
        import re
        json_match = re.search(r"\{[\s\S]*\}", response.text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                "slides": [],
                "overall_context": response.text,
                "key_statistics": [],
                "sources": [],
            }

    print("[Researcher] 리서치 완료")
    return result
