"""AI 카드뉴스 자동생성기 — 웹 인터페이스 (FastAPI)"""

import asyncio
import json
import os
import traceback
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from pipeline.config import OUTPUT_DIR, BRAND_PATH, PROJECT_ROOT

app = FastAPI(title="AI 카드뉴스 자동생성기")

# 디렉토리 마운트
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")


# ─── 페이지 라우트 ───

@app.get("/", response_class=HTMLResponse)
async def index():
    """메인 페이지"""
    html_path = PROJECT_ROOT / "static" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/brand", response_class=JSONResponse)
async def get_brand():
    """현재 brand.md 설정 반환"""
    from pipeline.config import parse_brand
    try:
        brand = parse_brand()
        return {"status": "ok", "brand": brand}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/brand", response_class=JSONResponse)
async def save_brand(request: Request):
    """brand.md 저장"""
    data = await request.json()
    try:
        md = f"""# 브랜드 가이드

## 브랜드 정보
- 브랜드명: {data.get('brand_name', '')}
- 인스타그램 핸들: {data.get('instagram_handle', '')}
- 메인 컬러: {data.get('main_color', '#7C3AED')}
- 서브 컬러: {data.get('sub_color', '#F5F3FF')}

## 타겟 독자 페르소나
- 연령대: {data.get('target_age', '')}
- 직업/관심사: {data.get('target_interest', '')}
- 고민/니즈: {data.get('target_needs', '')}

## 콘텐츠 목표
- {data.get('goal', '')}

## 톤앤매너
{chr(10).join('- ' + t for t in data.get('tone_items', ['친근하고 쉽게']))}

## CTA 문구
- {data.get('cta', '')}
"""
        BRAND_PATH.write_text(md, encoding="utf-8")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/generate", response_class=JSONResponse)
async def generate():
    """카드뉴스 생성 파이프라인 실행"""
    if not os.environ.get("GEMINI_API_KEY"):
        return {"status": "error", "message": "GEMINI_API_KEY 환경변수가 설정되지 않았습니다."}

    try:
        session_name = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Step 1: 크롤링
        from pipeline.crawler import crawl
        headlines = await crawl()
        if not headlines:
            return {"status": "error", "message": "수집된 헤드라인이 없습니다."}

        # Step 2: 주제 선정
        from pipeline.topic_selector import select_topic
        topic = await asyncio.to_thread(select_topic, headlines)

        # Step 3: 기획안
        from pipeline.editor import create_plan
        plan = await asyncio.to_thread(create_plan, topic)

        # Step 4: 리서치
        from pipeline.researcher import research
        research_data = await asyncio.to_thread(research, plan)

        # Step 5: 텍스트
        from pipeline.writer import write
        writer_output = await asyncio.to_thread(write, plan, research_data)

        # Step 6: 이미지
        from pipeline.image_generator import generate_images
        image_paths = await asyncio.to_thread(generate_images, writer_output, session_name)

        # Step 7: 렌더링
        from pipeline.renderer import render_all
        png_paths = await asyncio.to_thread(render_all, writer_output, image_paths, session_name)

        # 세션 데이터 저장
        session_dir = OUTPUT_DIR / session_name
        session_data = {
            "session_name": session_name,
            "topic": topic,
            "plan": plan,
            "research": research_data,
            "writer_output": writer_output,
            "image_paths": image_paths,
            "png_paths": png_paths,
        }
        (session_dir / "session_data.json").write_text(
            json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # PNG URL 리스트
        png_urls = [f"/output/{session_name}/{Path(p).name}" for p in png_paths]

        return {
            "status": "ok",
            "session_name": session_name,
            "topic": topic.get("selected_topic", ""),
            "slides_count": len(png_paths),
            "png_urls": png_urls,
        }

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.get("/api/sessions", response_class=JSONResponse)
async def list_sessions():
    """생성된 세션 목록"""
    sessions = []
    if OUTPUT_DIR.exists():
        for d in sorted(OUTPUT_DIR.iterdir(), reverse=True):
            if d.is_dir() and (d / "session_data.json").exists():
                data = json.loads((d / "session_data.json").read_text(encoding="utf-8"))
                pngs = [f"/output/{d.name}/{Path(p).name}" for p in data.get("png_paths", [])]
                sessions.append({
                    "name": d.name,
                    "topic": data.get("topic", {}).get("selected_topic", ""),
                    "slides_count": len(pngs),
                    "png_urls": pngs,
                })
    return {"sessions": sessions}


@app.get("/api/sessions/{session_name}", response_class=JSONResponse)
async def get_session(session_name: str):
    """특정 세션 상세"""
    path = OUTPUT_DIR / session_name / "session_data.json"
    if not path.exists():
        return {"status": "error", "message": "세션을 찾을 수 없습니다."}
    data = json.loads(path.read_text(encoding="utf-8"))
    pngs = [f"/output/{session_name}/{Path(p).name}" for p in data.get("png_paths", [])]
    data["png_urls"] = pngs
    return {"status": "ok", "data": data}
