"""프로젝트 설정 및 brand.md 파싱"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BRAND_PATH = PROJECT_ROOT / "brand.md"
NEWS_SOURCES_PATH = PROJECT_ROOT / "news_sources.txt"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / "output"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Vertex AI 설정
VERTEX_AI_ENABLED = os.environ.get("VERTEX_AI_ENABLED", "").lower() in ("true", "1", "yes")
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
# 서비스 계정 키 JSON 경로 (Railway에서는 환경변수로 JSON 내용을 직접 넣을 수도 있음)
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

# Gemini 모델명
MODEL_FLASH = "gemini-2.5-flash-preview-05-20"
MODEL_PRO = "gemini-2.5-pro-preview-05-06"
MODEL_IMAGE = "gemini-2.0-flash-exp"  # 이미지 생성용 (변경될 수 있음)


def get_genai_client():
    """환경변수에 따라 Gemini API 또는 Vertex AI 클라이언트 반환"""
    from google import genai

    if VERTEX_AI_ENABLED and GCP_PROJECT_ID:
        # Vertex AI: GCP 프로젝트 기반 인증
        # GOOGLE_APPLICATION_CREDENTIALS 환경변수가 설정되어 있으면 자동 인식
        # 또는 GCP_SA_KEY_JSON 환경변수에 JSON 내용을 직접 넣은 경우 처리
        sa_key_json = os.environ.get("GCP_SA_KEY_JSON", "")
        if sa_key_json:
            import json
            import tempfile
            # JSON 문자열을 임시 파일로 저장하여 ADC로 사용
            key_data = json.loads(sa_key_json)
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            json.dump(key_data, tmp)
            tmp.close()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

        client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_LOCATION,
        )
        return client
    else:
        # Gemini API: API Key 기반
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY 또는 VERTEX_AI_ENABLED + GCP_PROJECT_ID를 설정하세요."
            )
        return genai.Client(api_key=GEMINI_API_KEY)


def parse_brand() -> dict:
    """brand.md를 파싱하여 딕셔너리로 반환"""
    text = BRAND_PATH.read_text(encoding="utf-8")

    def extract(pattern: str, default: str = "") -> str:
        m = re.search(pattern, text)
        return m.group(1).strip() if m else default

    brand = {
        "brand_name": extract(r"브랜드명:\s*(.+)"),
        "instagram_handle": extract(r"인스타그램 핸들:\s*(.+)"),
        "main_color": extract(r"메인 컬러:\s*(#[A-Fa-f0-9]{6})"),
        "sub_color": extract(r"서브 컬러:\s*(#[A-Fa-f0-9]{6})"),
        "target_age": extract(r"연령대:\s*(.+)"),
        "target_interest": extract(r"직업/관심사:\s*(.+)"),
        "target_needs": extract(r"고민/니즈:\s*(.+)"),
        "goal": extract(r"콘텐츠 목표\n-\s*(.+)"),
        "cta": extract(r"CTA 문구\n-\s*(.+)"),
    }

    # 톤앤매너 섹션 추출
    tone_section = re.search(r"## 톤앤매너\n((?:- .+\n?)+)", text)
    if tone_section:
        brand["tone_guide"] = tone_section.group(1).strip()
    else:
        brand["tone_guide"] = '친근하고 쉽게, "~거든요" 스타일'

    # 타겟 독자 요약 문자열
    parts = []
    if brand["target_age"]:
        parts.append(brand["target_age"])
    if brand["target_interest"]:
        parts.append(brand["target_interest"])
    if brand["target_needs"]:
        parts.append(f"고민: {brand['target_needs']}")
    brand["target_audience"] = ", ".join(parts) if parts else "일반 독자"

    return brand


def parse_news_sources() -> list[str]:
    """news_sources.txt에서 RSS URL 목록 반환"""
    text = NEWS_SOURCES_PATH.read_text(encoding="utf-8")
    urls = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def load_prompt(name: str, **kwargs) -> str:
    """프롬프트 파일을 로드하고 변수를 치환"""
    path = PROMPTS_DIR / f"{name}.md"
    text = path.read_text(encoding="utf-8")
    for key, value in kwargs.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text
