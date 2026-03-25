"""Step 7: Renderer — HTML 템플릿 + 데이터 → PNG 출력"""

import asyncio
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

from .config import OUTPUT_DIR, TEMPLATES_DIR, parse_brand


def render_html(slide: dict, image_path: str, slide_index: int, total_slides: int) -> str:
    """슬라이드 데이터를 HTML로 렌더링"""
    brand = parse_brand()

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    slide_type = slide.get("slide_type", "content")
    template_name = f"{slide_type}.html"
    template = env.get_template(template_name)

    # 이미지 경로를 file:// URI로 변환
    if image_path and Path(image_path).exists():
        image_uri = f"file://{Path(image_path).absolute()}"
    else:
        image_uri = ""

    context = {
        "brand_name": brand["brand_name"],
        "instagram_handle": brand.get("instagram_handle", ""),
        "main_color": brand["main_color"],
        "sub_color": brand["sub_color"],
        "heading": slide.get("heading", ""),
        "body": slide.get("body", ""),
        "category_tag": slide.get("category_tag", ""),
        "image_path": image_uri,
        "slide_number": slide_index + 1,
        "total_slides": total_slides,
    }

    return template.render(**context)


async def capture_png(html_content: str, output_path: Path) -> None:
    """HTML을 1080x1350 PNG로 캡처 (2x 해상도 = 2160x2700)"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1350},
            device_scale_factor=2,  # 인스타그램 고해상도
        )
        await page.set_content(html_content, wait_until="networkidle")
        await page.screenshot(path=str(output_path), full_page=False)
        await browser.close()


def render_all(writer_output: dict, image_paths: list[str], session_name: str) -> list[str]:
    """전체 슬라이드를 PNG로 렌더링"""
    slides = writer_output.get("slides", [])
    output_dir = OUTPUT_DIR / session_name
    output_dir.mkdir(parents=True, exist_ok=True)

    png_paths = []
    total = len(slides)

    for i, slide in enumerate(slides):
        image_path = image_paths[i] if i < len(image_paths) else ""
        html = render_html(slide, image_path, i, total)

        # HTML 파일 저장 (디버깅용)
        html_path = output_dir / f"slide_{i + 1}.html"
        html_path.write_text(html, encoding="utf-8")

        # PNG 캡처
        png_path = output_dir / f"slide_{i + 1}.png"
        print(f"[Renderer] 슬라이드 {i + 1}/{total} PNG 생성 중...")
        asyncio.run(capture_png(html, png_path))
        png_paths.append(str(png_path))
        print(f"  [OK] {png_path}")

    return png_paths
