"""Step 3: Editor — Gemini Flash로 5장 슬라이드 기획안 작성"""

import json

from .config import MODEL_FLASH, get_genai_client, load_prompt, parse_brand


def create_plan(topic: dict) -> dict:
    """선정된 주제로 5장 슬라이드 기획안 작성"""
    brand = parse_brand()

    system_prompt = load_prompt(
        "editor",
        topic_domain=brand.get("target_interest", "AI/테크"),
        target_audience=brand["target_audience"],
    )

    user_message = f"""다음 주제로 5장 카드뉴스 기획안을 작성해주세요:

주제: {topic.get('selected_topic', '')}
앵글 제안: {topic.get('angle_suggestion', '')}
원본 헤드라인: {topic.get('source_headline', '')}
원본 URL: {topic.get('source_url', '')}
선정 이유: {topic.get('selection_reason', '')}"""

    print("[Editor] Gemini Flash로 기획안 작성 중...")

    client = get_genai_client()
    response = client.models.generate_content(
        model=MODEL_FLASH,
        contents=[
            {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_message}]}
        ],
        config={
            "temperature": 0.7,
            "response_mime_type": "application/json",
        },
    )

    result = json.loads(response.text)
    print(f"[Editor] 기획안 완성 — 앵글: {result.get('angle', 'N/A')}")
    return result
