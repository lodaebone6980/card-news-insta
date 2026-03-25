# AI 카드뉴스 자동생성기 (인스타그램용)

## 프로젝트 개요
RSS 뉴스를 크롤링하여 AI가 자동으로 인스타그램 카드뉴스(1080x1350px)를 생성하는 파이프라인.
Gemini API를 사용하며, `python main.py` 한 번 실행으로 전체 파이프라인이 동작한다.

## 기술 스택
- Python 3.12+ / FastAPI / Uvicorn
- Google Gemini API (Flash / Pro / Flash-Image) + Vertex AI 듀얼 지원
- httpx (비동기 RSS 크롤링)
- Playwright (HTML → PNG 렌더링, device_scale_factor=2 고해상도)
- Jinja2 (HTML 템플릿 엔진)
- Supabase (사용자/히스토리/접속기록 DB)

## 슬라이드 타입 시스템 (8종)
- `cover` — 표지 (훅 제목 + 배경 이미지)
- `content` — 기본 본문 (태그 + 제목 + 본문 + 배경)
- `content-stat` — 통계 강조 (큰 숫자 + 설명)
- `content-list` — 리스트형 (번호 + 제목 + 설명)
- `content-quote` — 인용구 (큰따옴표 + 출처)
- `content-split` — 좌우 비교 (A vs B)
- `content-grid` — 2x2 그리드 (아이콘 + 제목 + 설명)
- `last` — CTA (마무리 메시지 + 행동 유도)

## 참고 레포 (GitHub 학습)
- sgtlim0/instagram-card-news — 14종 슬라이드 타입, 8 디자인 템플릿
- FranciscoMoretti/carousel-generator — Zod 스키마 + 30 테마
- geongi-im/card-news-generator — Gemini + PIL + 인스타 자동포스팅
- mutonby/viraloop — Hook→Problem→Solution→CTA 구조 + 성과 학습 루프

## 디렉토리 구조
- `strategies/` — 브랜딩/에디토리얼 전략서
- `sops/` — 에디터/마케터/포토그래퍼 SOP
- `prompts/` — 각 파이프라인 단계별 프롬프트
- `templates/` — 카드뉴스 HTML 템플릿 (cover, content, last)
- `pipeline/` — 파이프라인 모듈
- `output/` — 생성된 카드뉴스 PNG
- `.claude/skills/` — Claude Code 커스텀 스킬

## 파이프라인 흐름
1. Crawler → 2. Topic Selector → 3. Editor → 4. Researcher → 5. Writer → 6. Image Generator → 7. Renderer

## 환경변수 (둘 중 하나 선택)

### 방법 1: Gemini API (간편)
- `GEMINI_API_KEY` — Google AI Studio에서 발급한 API 키

### 방법 2: Vertex AI (프로덕션)
- `VERTEX_AI_ENABLED=true`
- `GCP_PROJECT_ID` — GCP 프로젝트 ID
- `GCP_LOCATION` — 리전 (기본: us-central1)
- `GCP_SA_KEY_JSON` — 서비스 계정 키 JSON 내용 (Railway 등 클라우드 환경용)
- 또는 `GOOGLE_APPLICATION_CREDENTIALS` — 서비스 계정 키 JSON 파일 경로 (로컬용)

## 주요 명령어
- `python main.py` — 전체 파이프라인 실행
- `/setup-brand` — 브랜드 설정 대화형 가이드
- `/generate` — 카드뉴스 생성
- `/preview` — 마지막 생성 결과 확인

## 주의사항
- brand.md가 반드시 먼저 설정되어야 파이프라인이 정상 동작한다
- Gemini 이미지 생성 시 rate limit 방지를 위해 2~3초 간격을 둔다
- 이미지 모델명(gemini-2.5-flash-image)은 변경될 수 있으므로 AI Studio에서 확인
