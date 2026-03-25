"""AI 카드뉴스 자동생성기 — 웹 인터페이스 (FastAPI)"""

import asyncio
import hashlib
import json
import os
import secrets
import traceback
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from pipeline.config import OUTPUT_DIR, BRAND_PATH, PROJECT_ROOT

app = FastAPI(title="AI 카드뉴스 자동생성기")

# 디렉토리 마운트
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
app.mount("/samples", StaticFiles(directory=str(PROJECT_ROOT / "samples")), name="samples")
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")

# 세션 저장소 (서버 메모리 — 프로덕션에서는 Redis 등으로 교체)
_sessions: dict[str, dict] = {}

SESSION_COOKIE = "cn_session"


def get_current_user(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE)
    if token and token in _sessions:
        return _sessions[token]
    return None


# ─── 페이지 라우트 ───

@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = PROJECT_ROOT / "static" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


# ─── 인증 API ───

@app.post("/api/login")
async def api_login(request: Request):
    data = await request.json()
    username = data.get("username", "")
    password = data.get("password", "")
    ip = request.client.host if request.client else ""
    ua = request.headers.get("user-agent", "")[:200]

    try:
        from pipeline.database import login
        user = login(username, password, ip, ua)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

    if not user:
        return JSONResponse({"status": "error", "message": "아이디 또는 비밀번호가 틀렸습니다."})

    token = secrets.token_hex(32)
    _sessions[token] = user
    resp = JSONResponse({"status": "ok", "user": user})
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, max_age=86400 * 7, samesite="lax")
    return resp


@app.post("/api/logout")
async def api_logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token and token in _sessions:
        # 접속 로그
        try:
            from pipeline.database import get_sb
            user = _sessions[token]
            get_sb().table("cn_access_logs").insert({
                "user_id": user["id"],
                "action": "logout",
            }).execute()
        except Exception:
            pass
        del _sessions[token]
    resp = JSONResponse({"status": "ok"})
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.get("/api/me")
async def api_me(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"status": "error", "message": "로그인이 필요합니다."}, status_code=401)
    return JSONResponse({"status": "ok", "user": user})


# ─── 어드민: 회원관리 ───

@app.get("/api/admin/users")
async def admin_users(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return JSONResponse({"status": "error", "message": "권한 없음"}, status_code=403)
    from pipeline.database import get_all_users
    return JSONResponse({"status": "ok", "users": get_all_users()})


@app.post("/api/admin/users")
async def admin_create_user(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return JSONResponse({"status": "error", "message": "권한 없음"}, status_code=403)
    data = await request.json()
    from pipeline.database import create_user
    try:
        new_user = create_user(data["username"], data["password"], data.get("role", "user"))
        return JSONResponse({"status": "ok", "user": new_user})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: str, request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return JSONResponse({"status": "error", "message": "권한 없음"}, status_code=403)
    from pipeline.database import delete_user
    delete_user(user_id)
    return JSONResponse({"status": "ok"})


@app.get("/api/admin/logs")
async def admin_logs(request: Request):
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        return JSONResponse({"status": "error", "message": "권한 없음"}, status_code=403)
    from pipeline.database import get_access_logs
    return JSONResponse({"status": "ok", "logs": get_access_logs(100)})


# ─── 브랜드 ───

@app.get("/api/brand")
async def get_brand():
    from pipeline.config import parse_brand
    try:
        return JSONResponse({"status": "ok", "brand": parse_brand()})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/brand")
async def save_brand(request: Request):
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
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# ─── 카드뉴스 생성 ───

@app.post("/api/generate")
async def generate(request: Request):
    has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
    has_vertex = (
        os.environ.get("VERTEX_AI_ENABLED", "").lower() in ("true", "1", "yes")
        and bool(os.environ.get("GCP_PROJECT_ID"))
    )
    if not has_gemini and not has_vertex:
        return JSONResponse({"status": "error", "message": "GEMINI_API_KEY 또는 VERTEX_AI_ENABLED + GCP_PROJECT_ID를 설정하세요."})

    user = get_current_user(request)

    try:
        session_name = datetime.now().strftime("%Y%m%d_%H%M%S")

        from pipeline.crawler import crawl
        headlines = await crawl()
        if not headlines:
            return JSONResponse({"status": "error", "message": "수집된 헤드라인이 없습니다."})

        from pipeline.topic_selector import select_topic
        topic = await asyncio.to_thread(select_topic, headlines)

        from pipeline.editor import create_plan
        plan = await asyncio.to_thread(create_plan, topic)

        from pipeline.researcher import research
        research_data = await asyncio.to_thread(research, plan)

        from pipeline.writer import write
        writer_output = await asyncio.to_thread(write, plan, research_data)

        from pipeline.image_generator import generate_images
        image_paths = await asyncio.to_thread(generate_images, writer_output, session_name)

        from pipeline.renderer import render_all
        png_paths = await asyncio.to_thread(render_all, writer_output, image_paths, session_name)

        # 로컬 세션 데이터 저장
        session_dir = OUTPUT_DIR / session_name
        session_data = {
            "session_name": session_name, "topic": topic, "plan": plan,
            "research": research_data, "writer_output": writer_output,
            "image_paths": image_paths, "png_paths": png_paths,
        }
        (session_dir / "session_data.json").write_text(
            json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        png_urls = [f"/output/{session_name}/{Path(p).name}" for p in png_paths]

        # Supabase 히스토리 저장
        try:
            from pipeline.database import save_card_history
            save_card_history(
                user_id=user["id"] if user else None,
                session_name=session_name,
                category="auto",
                topic=topic.get("selected_topic", ""),
                slides_count=len(png_paths),
                slides_data=writer_output,
                png_urls=png_urls,
            )
        except Exception as db_err:
            print(f"[Warning] Supabase 저장 실패: {db_err}")

        return JSONResponse({
            "status": "ok", "session_name": session_name,
            "topic": topic.get("selected_topic", ""),
            "slides_count": len(png_paths), "png_urls": png_urls,
            "slides_data": writer_output.get("slides", []),
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/re-render")
async def re_render(request: Request):
    """수정된 슬라이드 데이터를 받아 PNG 재생성"""
    data = await request.json()
    slide = data.get("slide", {})
    slide_index = data.get("slide_index", 0)
    session_name = data.get("session_name", "edited")
    theme = data.get("theme", "dark")

    try:
        from pipeline.renderer import render_html, capture_png
        from pipeline.config import OUTPUT_DIR

        output_dir = OUTPUT_DIR / session_name
        output_dir.mkdir(parents=True, exist_ok=True)

        html = render_html(slide, "", slide_index, data.get("total_slides", 7), theme)
        html_path = output_dir / f"slide_{slide_index + 1}.html"
        html_path.write_text(html, encoding="utf-8")

        png_path = output_dir / f"slide_{slide_index + 1}.png"

        import asyncio
        await asyncio.to_thread(
            lambda: __import__('asyncio').run(capture_png(html, png_path))
        )

        png_url = f"/output/{session_name}/slide_{slide_index + 1}.png?t={int(datetime.now().timestamp())}"
        return JSONResponse({"status": "ok", "png_url": png_url})

    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"status": "error", "message": str(e)})


# ─── 히스토리 (Supabase) ───

@app.get("/api/history")
async def api_history(request: Request):
    try:
        from pipeline.database import get_card_history
        history = get_card_history(limit=30)
        return JSONResponse({"status": "ok", "history": history})
    except Exception as e:
        return JSONResponse({"status": "ok", "history": []})


@app.get("/api/history/{history_id}")
async def api_history_item(history_id: int):
    try:
        from pipeline.database import get_card_history_item
        item = get_card_history_item(history_id)
        if item:
            return JSONResponse({"status": "ok", "data": item})
        return JSONResponse({"status": "error", "message": "not found"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# ─── 로컬 세션 (레거시 호환) ───

@app.get("/api/sessions")
async def list_sessions():
    sessions = []
    if OUTPUT_DIR.exists():
        for d in sorted(OUTPUT_DIR.iterdir(), reverse=True):
            if d.is_dir() and (d / "session_data.json").exists():
                data = json.loads((d / "session_data.json").read_text(encoding="utf-8"))
                pngs = [f"/output/{d.name}/{Path(p).name}" for p in data.get("png_paths", [])]
                sessions.append({
                    "name": d.name,
                    "topic": data.get("topic", {}).get("selected_topic", ""),
                    "slides_count": len(pngs), "png_urls": pngs,
                })
    return JSONResponse({"sessions": sessions})


@app.get("/api/sessions/{session_name}")
async def get_session(session_name: str):
    path = OUTPUT_DIR / session_name / "session_data.json"
    if not path.exists():
        return JSONResponse({"status": "error", "message": "세션을 찾을 수 없습니다."})
    data = json.loads(path.read_text(encoding="utf-8"))
    pngs = [f"/output/{session_name}/{Path(p).name}" for p in data.get("png_paths", [])]
    data["png_urls"] = pngs
    return JSONResponse({"status": "ok", "data": data})


# ─── 샘플 ───

@app.get("/api/samples")
async def list_samples():
    samples_dir = PROJECT_ROOT / "samples"
    categories = {
        "shopping": {"name": "쇼핑", "color": "#E74C3C", "desc": "가성비 꿀템, 핫딜, 추천 리스트"},
        "fortune": {"name": "사주/운세", "color": "#1B1464", "desc": "띠별 운세, 타로, 별자리"},
        "subsidy": {"name": "지원금", "color": "#2563EB", "desc": "청년 지원금, 정부 보조금 총정리"},
    }
    result = []
    for cat_key, cat_info in categories.items():
        cat_dir = samples_dir / cat_key
        if cat_dir.exists():
            pngs = sorted([f"/samples/{cat_key}/{f.name}" for f in cat_dir.glob("*.png")])
            result.append({**cat_info, "key": cat_key, "slides": pngs})
    return JSONResponse({"categories": result})
