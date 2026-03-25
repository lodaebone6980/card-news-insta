# AI 카드뉴스 자동생성기 (인스타그램용)

## 프로젝트 개요
RSS 뉴스를 크롤링하여 AI가 자동으로 인스타그램 카드뉴스(1080x1350px)를 생성하는 파이프라인.
Gemini API를 사용하며, `python main.py` 한 번 실행으로 전체 파이프라인이 동작한다.

## 기술 스택
- Python 3.11+
- Google Gemini API (Flash / Pro / Flash-Image)
- httpx (비동기 RSS 크롤링)
- Playwright (HTML → PNG 렌더링)
- Jinja2 (HTML 템플릿 엔진)

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

## 환경변수
- `GEMINI_API_KEY` — Google Gemini API 키 (필수)

## 주요 명령어
- `python main.py` — 전체 파이프라인 실행
- `/setup-brand` — 브랜드 설정 대화형 가이드
- `/generate` — 카드뉴스 생성
- `/preview` — 마지막 생성 결과 확인

## 주의사항
- brand.md가 반드시 먼저 설정되어야 파이프라인이 정상 동작한다
- Gemini 이미지 생성 시 rate limit 방지를 위해 2~3초 간격을 둔다
- 이미지 모델명(gemini-2.5-flash-image)은 변경될 수 있으므로 AI Studio에서 확인
