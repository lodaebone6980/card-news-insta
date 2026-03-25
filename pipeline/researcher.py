"""Step 4: Researcher — Gemini Pro + Google Search로 팩트 리서치"""

import json

from .config import MODEL_PRO, get_genai_client, load_prompt, safe_parse_json


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

    print("[Researcher] Gemini로 리서치 중...")

    client = get_genai_client()
    contents = [{"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_message}]}]

    # Google Search 도구 사용 시도, 실패하면 도구 없이 재시도
    try:
        response = client.models.generate_content(
            model=MODEL_PRO,
            contents=contents,
            config={
                "temperature": 0.4,
                "response_mime_type": "application/json",
                "tools": [{"google_search": {}}],
            },
        )
    except Exception as e:
        print(f"  [경고] Google Search 실패, 도구 없이 재시도: {e}")
        response = client.models.generate_content(
            model=MODEL_PRO,
            contents=contents,
            config={"temperature": 0.4, "response_mime_type": "application/json"},
        )

    result = safe_parse_json(response.text)
    if "error" in result:
        result = {
            "slides": [],
            "overall_context": result.get("raw", ""),
            "key_statistics": [],
            "sources": [],
        }

    print("[Researcher] 리서치 완료")
    return result
