"""Step 5: Writer — Gemini Pro로 최종 텍스트 작성"""

import json

from .config import MODEL_PRO, get_genai_client, load_prompt, parse_brand


def write(plan: dict, research_data: dict) -> dict:
    """기획안 + 리서치 데이터로 최종 카드뉴스 텍스트 작성"""
    brand = parse_brand()

    system_prompt = load_prompt(
        "writer",
        topic_domain=brand.get("target_interest", "AI/테크"),
        target_audience=brand["target_audience"],
        tone_guide=brand["tone_guide"],
    )

    user_message = f"""다음 기획안과 리서치 데이터를 바탕으로 최종 카드뉴스 텍스트를 작성해주세요.

## 기획안
앵글: {plan.get('angle', '')}
훅 전략: {plan.get('hook_strategy', '')}
내러티브: {plan.get('narrative_arc', '')}

슬라이드 기획:
{json.dumps(plan.get('slides', []), ensure_ascii=False, indent=2)}

## 리서치 데이터
핵심 통계: {json.dumps(research_data.get('key_statistics', []), ensure_ascii=False)}
전체 맥락: {research_data.get('overall_context', '')}

슬라이드별 팩트:
{json.dumps(research_data.get('slides', []), ensure_ascii=False, indent=2)}

## CTA 문구
{brand.get('cta', '팔로우하면 매일 트렌드를 받아볼 수 있어요')}"""

    print("[Writer] Gemini Pro로 최종 텍스트 작성 중...")

    client = get_genai_client()
    response = client.models.generate_content(
        model=MODEL_PRO,
        contents=[
            {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_message}]}
        ],
        config={
            "temperature": 0.8,
            "response_mime_type": "application/json",
        },
    )

    result = json.loads(response.text)
    slides = result.get("slides", [])
    print(f"[Writer] {len(slides)}장 슬라이드 텍스트 완성")
    return result
