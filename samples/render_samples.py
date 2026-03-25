"""샘플 카드뉴스 HTML을 PNG로 렌더링"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SAMPLES_DIR = Path(__file__).parent

async def render_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        for category in ["shopping", "fortune", "subsidy"]:
            cat_dir = SAMPLES_DIR / category
            for html_file in sorted(cat_dir.glob("*.html")):
                png_path = html_file.with_suffix(".png")
                page = await browser.new_page(viewport={"width": 1080, "height": 1350})
                html = html_file.read_text(encoding="utf-8")
                await page.set_content(html, wait_until="networkidle")
                await page.screenshot(path=str(png_path), full_page=False)
                await page.close()
                print(f"[OK] {png_path.relative_to(SAMPLES_DIR)}")

        await browser.close()

asyncio.run(render_all())
