"""Step 6: Image Generator — Gemini로 슬라이드별 AI 이미지 생성"""

import base64
import time
from pathlib import Path

from google import genai

from .config import GEMINI_API_KEY, MODEL_IMAGE, OUTPUT_DIR

IMAGE_SUFFIX = """
Shot with 85mm lens, f/2.0, ISO 200, shallow depth of field.
Natural soft lighting creating gentle highlights and subtle shadows.
High detail, unretouched quality.
Avoid: blurry, distorted, text, watermark, logo, infographic, chart, graph, diagram, abstract gradient"""


def generate_images(writer_output: dict, session_name: str) -> list[str]:
    """각 슬라이드의 image_prompt로 배경 이미지 생성"""
    slides = writer_output.get("slides", [])
    image_dir = OUTPUT_DIR / session_name / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    client = genai.Client(api_key=GEMINI_API_KEY)
    image_paths = []

    for i, slide in enumerate(slides):
        prompt = slide.get("image_prompt", "")
        if not prompt:
            image_paths.append("")
            continue

        full_prompt = f"{prompt}\n{IMAGE_SUFFIX}"

        print(f"[Image Gen] 슬라이드 {i + 1}/{len(slides)} 이미지 생성 중...")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=MODEL_IMAGE,
                    contents=[{"role": "user", "parts": [{"text": full_prompt}]}],
                    config={
                        "response_modalities": ["image", "text"],
                    },
                )

                # 이미지 데이터 추출
                image_saved = False
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        image_data = base64.b64decode(part.inline_data.data)
                        ext = part.inline_data.mime_type.split("/")[-1]
                        image_path = image_dir / f"slide_{i + 1}.{ext}"
                        image_path.write_bytes(image_data)
                        image_paths.append(str(image_path))
                        image_saved = True
                        print(f"  [OK] slide_{i + 1}.{ext} 저장됨")
                        break

                if not image_saved:
                    raise ValueError("응답에 이미지 데이터가 없음")

                break  # 성공 시 루프 종료

            except Exception as e:
                print(f"  [재시도 {attempt + 1}/{max_retries}] {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    print(f"  [실패] 슬라이드 {i + 1} 이미지 생성 실패")
                    image_paths.append("")

        # Rate limit 방지
        if i < len(slides) - 1:
            time.sleep(3)

    return image_paths
