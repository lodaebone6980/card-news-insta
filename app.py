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

from pipeline.config import OUTPUT_DIR, BRAND_PATH

app = FastAPI(title="AI 카드뉴스 자동생성기")

# output 디렉토리 마운트
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


# ─── 페이지 라우트 ───

@app.get("/", response_class=HTMLResponse)
async def index():
    """메인 페이지"""
    return get_main_page()


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


# ─── 메인 HTML ───

def get_main_page() -> str:
    return """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 카드뉴스 자동생성기</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

  :root {
    --primary: #7C3AED;
    --primary-light: #F5F3FF;
    --bg: #0F0F10;
    --surface: #1A1A1D;
    --surface2: #242428;
    --text: #EAEAEB;
    --text-dim: #8E8E93;
    --border: #2C2C30;
    --success: #34C759;
    --error: #FF3B30;
    --radius: 16px;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Noto Sans KR', -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }

  .container {
    max-width: 960px;
    margin: 0 auto;
    padding: 40px 24px;
  }

  header {
    text-align: center;
    margin-bottom: 48px;
  }

  header h1 {
    font-size: 32px;
    font-weight: 900;
    background: linear-gradient(135deg, var(--primary), #A78BFA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
  }

  header p {
    color: var(--text-dim);
    font-size: 15px;
  }

  .tabs {
    display: flex;
    gap: 4px;
    background: var(--surface);
    padding: 4px;
    border-radius: 12px;
    margin-bottom: 32px;
  }

  .tab {
    flex: 1;
    padding: 12px;
    text-align: center;
    border-radius: 10px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-dim);
    transition: all 0.2s;
    border: none;
    background: none;
  }

  .tab.active {
    background: var(--primary);
    color: white;
  }

  .panel { display: none; }
  .panel.active { display: block; }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 28px;
    margin-bottom: 20px;
  }

  .card h3 {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 20px;
  }

  .form-group {
    margin-bottom: 20px;
  }

  label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-dim);
    margin-bottom: 8px;
  }

  input, select, textarea {
    width: 100%;
    padding: 12px 16px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--text);
    font-size: 15px;
    font-family: inherit;
    outline: none;
    transition: border-color 0.2s;
  }

  input:focus, select:focus, textarea:focus {
    border-color: var(--primary);
  }

  textarea { resize: vertical; min-height: 80px; }

  .color-options {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 10px;
  }

  .color-option {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px;
    border-radius: 10px;
    border: 2px solid var(--border);
    cursor: pointer;
    transition: all 0.2s;
    background: var(--surface2);
  }

  .color-option:hover { border-color: var(--text-dim); }
  .color-option.selected { border-color: var(--primary); background: rgba(124,58,237,0.1); }

  .color-swatch {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .color-option span {
    font-size: 13px;
    font-weight: 500;
  }

  .radio-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .radio-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    background: var(--surface2);
    border: 2px solid var(--border);
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .radio-item:hover { border-color: var(--text-dim); }
  .radio-item.selected { border-color: var(--primary); background: rgba(124,58,237,0.1); }

  .radio-item .title { font-size: 14px; font-weight: 500; }
  .radio-item .desc { font-size: 12px; color: var(--text-dim); margin-top: 2px; }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 14px 28px;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
    font-family: inherit;
  }

  .btn-primary {
    background: var(--primary);
    color: white;
    width: 100%;
  }

  .btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

  .btn-outline {
    background: transparent;
    color: var(--primary);
    border: 2px solid var(--primary);
  }

  .status {
    padding: 16px;
    border-radius: 10px;
    font-size: 14px;
    margin-top: 16px;
    display: none;
  }

  .status.show { display: block; }
  .status.success { background: rgba(52,199,89,0.1); color: var(--success); }
  .status.error { background: rgba(255,59,48,0.1); color: var(--error); }
  .status.loading { background: rgba(124,58,237,0.1); color: var(--primary); }

  .slides-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 16px;
    margin-top: 20px;
  }

  .slide-card {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border);
    transition: transform 0.2s;
  }

  .slide-card:hover { transform: scale(1.02); }

  .slide-card img {
    width: 100%;
    aspect-ratio: 1080/1350;
    object-fit: cover;
    display: block;
  }

  .session-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    background: var(--surface2);
    border-radius: 10px;
    margin-bottom: 10px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .session-item:hover { background: var(--border); }

  .loading-spinner {
    display: inline-block;
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-right: 8px;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .step-indicator {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 16px;
  }

  .step {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    color: var(--text-dim);
  }

  .step.active { color: var(--primary); font-weight: 500; }
  .step.done { color: var(--success); }

  .step-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--border);
    flex-shrink: 0;
  }

  .step.active .step-dot { background: var(--primary); }
  .step.done .step-dot { background: var(--success); }

  @media (max-width: 600px) {
    .container { padding: 20px 16px; }
    header h1 { font-size: 24px; }
    .slides-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
    .color-options { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>AI Card News Generator</h1>
    <p>RSS 뉴스를 AI가 자동으로 인스타 카드뉴스로 만들어줍니다</p>
  </header>

  <div class="tabs">
    <button class="tab active" onclick="showTab('brand')">브랜드 설정</button>
    <button class="tab" onclick="showTab('generate')">생성하기</button>
    <button class="tab" onclick="showTab('history')">히스토리</button>
  </div>

  <!-- 브랜드 설정 탭 -->
  <div id="panel-brand" class="panel active">
    <div class="card">
      <h3>브랜드 정보</h3>
      <div class="form-group">
        <label>브랜드명</label>
        <input id="brand_name" placeholder="예: AI트렌드">
      </div>
      <div class="form-group">
        <label>인스타그램 핸들</label>
        <input id="instagram_handle" placeholder="예: @my.brand">
      </div>
    </div>

    <div class="card">
      <h3>브랜드 컬러</h3>
      <div class="color-options" id="colorOptions">
        <div class="color-option selected" data-main="#7C3AED" data-sub="#F5F3FF" onclick="selectColor(this)">
          <div class="color-swatch" style="background:#7C3AED"></div>
          <span>바이올렛</span>
        </div>
        <div class="color-option" data-main="#2563EB" data-sub="#EFF6FF" onclick="selectColor(this)">
          <div class="color-swatch" style="background:#2563EB"></div>
          <span>오션블루</span>
        </div>
        <div class="color-option" data-main="#059669" data-sub="#ECFDF5" onclick="selectColor(this)">
          <div class="color-swatch" style="background:#059669"></div>
          <span>에메랄드</span>
        </div>
        <div class="color-option" data-main="#E11D48" data-sub="#FFF1F2" onclick="selectColor(this)">
          <div class="color-swatch" style="background:#E11D48"></div>
          <span>코랄핑크</span>
        </div>
        <div class="color-option" data-main="#D97706" data-sub="#FFFBEB" onclick="selectColor(this)">
          <div class="color-swatch" style="background:#D97706"></div>
          <span>앰버골드</span>
        </div>
        <div class="color-option" data-main="#334155" data-sub="#F8FAFC" onclick="selectColor(this)">
          <div class="color-swatch" style="background:#334155"></div>
          <span>슬레이트</span>
        </div>
      </div>
      <div class="form-group" style="margin-top:16px">
        <label>또는 직접 입력</label>
        <div style="display:flex;gap:10px">
          <input id="custom_main" placeholder="메인 #HEX" style="flex:1">
          <input id="custom_sub" placeholder="서브 #HEX" style="flex:1">
        </div>
      </div>
    </div>

    <div class="card">
      <h3>타겟 독자 페르소나</h3>
      <div class="form-group">
        <label>연령대</label>
        <input id="target_age" placeholder="예: 25~35세">
      </div>
      <div class="form-group">
        <label>직업/관심사</label>
        <input id="target_interest" placeholder="예: IT 직장인, AI에 관심 있는">
      </div>
      <div class="form-group">
        <label>주요 고민/니즈</label>
        <input id="target_needs" placeholder="예: AI 트렌드를 빠르게 파악하고 싶지만 시간이 없다">
      </div>
    </div>

    <div class="card">
      <h3>콘텐츠 목표</h3>
      <div class="radio-group" id="goalGroup">
        <div class="radio-item selected" data-value="정보 전달 — 트렌드/뉴스 큐레이션으로 팔로워 확보" onclick="selectRadio(this,'goalGroup')">
          <div><div class="title">정보 전달</div><div class="desc">트렌드/뉴스 큐레이션, 저장/공유율 높음 (AI 추천)</div></div>
        </div>
        <div class="radio-item" data-value="교육/가이드 — How-to, 실전 팁으로 전문성 구축" onclick="selectRadio(this,'goalGroup')">
          <div><div class="title">교육/가이드</div><div class="desc">How-to, 실전 팁, 높은 저장율</div></div>
        </div>
        <div class="radio-item" data-value="브랜드 인지도 — 전문성 어필, 개인 브랜딩" onclick="selectRadio(this,'goalGroup')">
          <div><div class="title">브랜드 인지도</div><div class="desc">전문성 어필, 개인 브랜딩/포트폴리오</div></div>
        </div>
        <div class="radio-item" data-value="커뮤니티 빌딩 — 공감/소통으로 충성 팔로워 확보" onclick="selectRadio(this,'goalGroup')">
          <div><div class="title">커뮤니티 빌딩</div><div class="desc">공감/소통, 댓글 유도율 높음</div></div>
        </div>
        <div class="radio-item" data-value="리드 생성 — DM/문의 유도로 비즈니스 전환" onclick="selectRadio(this,'goalGroup')">
          <div><div class="title">리드 생성</div><div class="desc">DM/문의 유도, 비즈니스 전환</div></div>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>톤앤매너</h3>
      <div class="radio-group" id="toneGroup">
        <div class="radio-item selected" data-value="친근한 친구" onclick="selectRadio(this,'toneGroup')">
          <div><div class="title">친근한 친구</div><div class="desc">"~거든요", "~인 셈이에요" 스타일</div></div>
        </div>
        <div class="radio-item" data-value="전문가" onclick="selectRadio(this,'toneGroup')">
          <div><div class="title">전문가</div><div class="desc">"~입니다", "~되었습니다" 스타일</div></div>
        </div>
        <div class="radio-item" data-value="캐주얼" onclick="selectRadio(this,'toneGroup')">
          <div><div class="title">캐주얼</div><div class="desc">"~임", "솔직히 이건" 스타일</div></div>
        </div>
        <div class="radio-item" data-value="스토리텔러" onclick="selectRadio(this,'toneGroup')">
          <div><div class="title">스토리텔러</div><div class="desc">"~했어요", "~더라고요" 스타일</div></div>
        </div>
      </div>
      <div class="form-group" style="margin-top:12px">
        <label>또는 직접 입력</label>
        <input id="custom_tone" placeholder="예: 존댓말 + 유머러스하게">
      </div>
    </div>

    <div class="card">
      <h3>CTA 문구</h3>
      <div class="radio-group" id="ctaGroup">
        <div class="radio-item selected" data-value="팔로우하면 매일 트렌드를 받아볼 수 있어요" onclick="selectRadio(this,'ctaGroup')">
          <div class="title">팔로우하면 매일 트렌드를 받아볼 수 있어요</div>
        </div>
        <div class="radio-item" data-value="저장해두고 나중에 다시 보세요" onclick="selectRadio(this,'ctaGroup')">
          <div class="title">저장해두고 나중에 다시 보세요</div>
        </div>
        <div class="radio-item" data-value="궁금한 점은 DM으로 물어보세요" onclick="selectRadio(this,'ctaGroup')">
          <div class="title">궁금한 점은 DM으로 물어보세요</div>
        </div>
        <div class="radio-item" data-value="이 글이 도움됐다면 친구에게 공유해주세요" onclick="selectRadio(this,'ctaGroup')">
          <div class="title">이 글이 도움됐다면 친구에게 공유해주세요</div>
        </div>
      </div>
      <div class="form-group" style="margin-top:12px">
        <label>또는 직접 입력</label>
        <input id="custom_cta" placeholder="CTA 문구를 직접 입력하세요">
      </div>
    </div>

    <button class="btn btn-primary" onclick="saveBrand()">브랜드 설정 저장</button>
    <div id="brandStatus" class="status"></div>
  </div>

  <!-- 생성하기 탭 -->
  <div id="panel-generate" class="panel">
    <div class="card">
      <h3>카드뉴스 생성</h3>
      <p style="color:var(--text-dim);font-size:14px;margin-bottom:20px">
        브랜드 설정을 완료한 후, 아래 버튼을 눌러 자동으로 카드뉴스를 생성하세요.<br>
        RSS에서 최신 뉴스를 수집하고, AI가 기획부터 디자인까지 자동 처리합니다.
      </p>
      <button id="generateBtn" class="btn btn-primary" onclick="startGenerate()">
        카드뉴스 생성 시작
      </button>

      <div id="genStatus" class="status"></div>

      <div class="step-indicator" id="stepIndicator" style="display:none">
        <div class="step" id="step1"><div class="step-dot"></div>Step 1: RSS 크롤링</div>
        <div class="step" id="step2"><div class="step-dot"></div>Step 2: 주제 선정 (Gemini Flash)</div>
        <div class="step" id="step3"><div class="step-dot"></div>Step 3: 기획안 작성 (Gemini Flash)</div>
        <div class="step" id="step4"><div class="step-dot"></div>Step 4: 리서치 (Gemini Pro + Search)</div>
        <div class="step" id="step5"><div class="step-dot"></div>Step 5: 텍스트 작성 (Gemini Pro)</div>
        <div class="step" id="step6"><div class="step-dot"></div>Step 6: AI 이미지 생성</div>
        <div class="step" id="step7"><div class="step-dot"></div>Step 7: HTML → PNG 렌더링</div>
      </div>
    </div>

    <div id="resultArea" style="display:none">
      <div class="card">
        <h3 id="resultTopic"></h3>
        <div class="slides-grid" id="slidesGrid"></div>
      </div>
    </div>
  </div>

  <!-- 히스토리 탭 -->
  <div id="panel-history" class="panel">
    <div class="card">
      <h3>생성 히스토리</h3>
      <div id="sessionList"><p style="color:var(--text-dim);font-size:14px">로딩 중...</p></div>
    </div>
    <div id="historyDetail" style="display:none">
      <div class="card">
        <h3 id="historyTopic"></h3>
        <div class="slides-grid" id="historySlides"></div>
      </div>
    </div>
  </div>
</div>

<script>
function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('panel-' + name).classList.add('active');
  if (name === 'history') loadSessions();
  if (name === 'brand') loadBrand();
}

function selectColor(el) {
  document.querySelectorAll('.color-option').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  document.getElementById('custom_main').value = el.dataset.main;
  document.getElementById('custom_sub').value = el.dataset.sub;
}

function selectRadio(el, groupId) {
  document.querySelectorAll('#' + groupId + ' .radio-item').forEach(r => r.classList.remove('selected'));
  el.classList.add('selected');
}

function getSelected(groupId) {
  const sel = document.querySelector('#' + groupId + ' .radio-item.selected');
  return sel ? sel.dataset.value : '';
}

function showStatus(id, type, msg) {
  const el = document.getElementById(id);
  el.className = 'status show ' + type;
  el.innerHTML = msg;
}

async function loadBrand() {
  try {
    const res = await fetch('/api/brand');
    const data = await res.json();
    if (data.status === 'ok' && data.brand.brand_name) {
      const b = data.brand;
      document.getElementById('brand_name').value = b.brand_name || '';
      document.getElementById('instagram_handle').value = b.instagram_handle || '';
      document.getElementById('target_age').value = b.target_age || '';
      document.getElementById('target_interest').value = b.target_interest || '';
      document.getElementById('target_needs').value = b.target_needs || '';
      if (b.main_color) document.getElementById('custom_main').value = b.main_color;
      if (b.sub_color) document.getElementById('custom_sub').value = b.sub_color;
    }
  } catch(e) {}
}

async function saveBrand() {
  const selectedColor = document.querySelector('.color-option.selected');
  const mainColor = document.getElementById('custom_main').value || (selectedColor ? selectedColor.dataset.main : '#7C3AED');
  const subColor = document.getElementById('custom_sub').value || (selectedColor ? selectedColor.dataset.sub : '#F5F3FF');

  const tone = document.getElementById('custom_tone').value || getSelected('toneGroup');
  const cta = document.getElementById('custom_cta').value || getSelected('ctaGroup');

  const body = {
    brand_name: document.getElementById('brand_name').value,
    instagram_handle: document.getElementById('instagram_handle').value,
    main_color: mainColor,
    sub_color: subColor,
    target_age: document.getElementById('target_age').value,
    target_interest: document.getElementById('target_interest').value,
    target_needs: document.getElementById('target_needs').value,
    goal: getSelected('goalGroup'),
    tone_items: [tone],
    cta: cta,
  };

  try {
    const res = await fetch('/api/brand', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
    const data = await res.json();
    if (data.status === 'ok') {
      showStatus('brandStatus', 'success', 'brand.md 설정이 저장되었습니다!');
    } else {
      showStatus('brandStatus', 'error', data.message);
    }
  } catch(e) {
    showStatus('brandStatus', 'error', '저장 실패: ' + e.message);
  }
}

async function startGenerate() {
  const btn = document.getElementById('generateBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span>생성 중...';

  document.getElementById('stepIndicator').style.display = 'block';
  document.getElementById('resultArea').style.display = 'none';
  showStatus('genStatus', 'loading', 'AI가 카드뉴스를 생성하고 있습니다. 2~5분 정도 소요됩니다...');

  // 단계 애니메이션 (예상 시간 기반)
  const steps = [1,2,3,4,5,6,7];
  const delays = [0, 8000, 20000, 35000, 60000, 90000, 140000];
  steps.forEach((s, i) => {
    setTimeout(() => {
      if (i > 0) document.getElementById('step' + steps[i-1]).className = 'step done';
      document.getElementById('step' + s).className = 'step active';
    }, delays[i]);
  });

  try {
    const res = await fetch('/api/generate', { method: 'POST' });
    const data = await res.json();

    steps.forEach(s => document.getElementById('step' + s).className = 'step done');

    if (data.status === 'ok') {
      showStatus('genStatus', 'success', '카드뉴스 ' + data.slides_count + '장 생성 완료!');
      document.getElementById('resultArea').style.display = 'block';
      document.getElementById('resultTopic').textContent = data.topic;
      const grid = document.getElementById('slidesGrid');
      grid.innerHTML = data.png_urls.map(url =>
        '<div class="slide-card"><a href="'+url+'" target="_blank"><img src="'+url+'" loading="lazy"></a></div>'
      ).join('');
    } else {
      showStatus('genStatus', 'error', data.message);
    }
  } catch(e) {
    showStatus('genStatus', 'error', '생성 실패: ' + e.message);
  }

  btn.disabled = false;
  btn.innerHTML = '카드뉴스 생성 시작';
}

async function loadSessions() {
  try {
    const res = await fetch('/api/sessions');
    const data = await res.json();
    const list = document.getElementById('sessionList');

    if (data.sessions.length === 0) {
      list.innerHTML = '<p style="color:var(--text-dim);font-size:14px">아직 생성된 카드뉴스가 없습니다.</p>';
      return;
    }

    list.innerHTML = data.sessions.map(s =>
      '<div class="session-item" onclick="showSession(\\''+s.name+'\\')">'+
      '<div><strong>'+s.topic+'</strong><div style="font-size:12px;color:var(--text-dim);margin-top:4px">'+s.name+' | '+s.slides_count+'장</div></div>'+
      '</div>'
    ).join('');
  } catch(e) {
    document.getElementById('sessionList').innerHTML = '<p style="color:var(--error)">로드 실패</p>';
  }
}

async function showSession(name) {
  try {
    const res = await fetch('/api/sessions/' + name);
    const data = await res.json();
    if (data.status === 'ok') {
      document.getElementById('historyDetail').style.display = 'block';
      document.getElementById('historyTopic').textContent = data.data.topic?.selected_topic || name;
      const grid = document.getElementById('historySlides');
      grid.innerHTML = (data.data.png_urls || []).map(url =>
        '<div class="slide-card"><a href="'+url+'" target="_blank"><img src="'+url+'" loading="lazy"></a></div>'
      ).join('');
    }
  } catch(e) {}
}

// 초기 로드
loadBrand();
</script>
</body>
</html>"""
