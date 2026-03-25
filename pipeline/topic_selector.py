"""Step 2: Topic Selector — Gemini Flash로 카드뉴스 주제 1개 선정"""

import json

from .config import MODEL_FLASH, get_genai_client, load_prompt, parse_brand, safe_parse_json


def select_topic(headlines: list[dict]) -> dict:
    """헤드라인 목록에서 카드뉴스 주제 1개 선정"""
    brand = parse_brand()

    # 헤드라인 텍스트 준비 (최대 50개)
    headline_text = "\n".join(
        f"- {h['title']} ({h['url']})"
        for h in headlines[:50]
    )

    # 프롬프트 로드 및 변수 치환
    system_prompt = load_prompt(
        "topic_selector",
        topic_domain=brand.get("target_interest", "AI/테크"),
        target_audience=brand["target_audience"],
    )

    user_message = f"""다음은 최근 수집된 뉴스 헤드라인 목록입니다:

{headline_text}

위 목록에서 카드뉴스로 만들기 가장 좋은 주제 1개를 선정해주세요."""

    print("[Topic Selector] Gemini Flash로 주제 선정 중...")

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

    result = safe_parse_json(response.text)
    print(f"[Topic Selector] 선정된 주제: {result.get('selected_topic', 'N/A')}")
    return result
