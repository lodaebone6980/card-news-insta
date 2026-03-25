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

# Gemini 모델명
MODEL_FLASH = "gemini-2.5-flash-preview-05-20"
MODEL_PRO = "gemini-2.5-pro-preview-05-06"
MODEL_IMAGE = "gemini-2.0-flash-exp"  # 이미지 생성용 (변경될 수 있음)


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
