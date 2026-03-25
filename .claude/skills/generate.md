---
name: generate
description: AI 카드뉴스 자동생성 파이프라인을 실행합니다.
---

# /generate — 카드뉴스 생성

## 실행 전 체크
1. brand.md가 설정되어 있는지 확인 (브랜드명이 "미설정"이면 `/setup-brand`를 먼저 안내)
2. GEMINI_API_KEY 환경변수가 설정되어 있는지 확인
3. 필요한 패키지가 설치되어 있는지 확인

## 패키지 미설치 시
```bash
pip install -r requirements.txt
playwright install chromium
```

## 실행
```bash
python main.py
```

## 실행 중 안내
파이프라인 각 단계의 진행 상황을 사용자에게 알려주세요:
- Step 1: RSS 크롤링 중...
- Step 2: 주제 선정 중...
- Step 3: 기획안 작성 중...
- Step 4: 리서치 중...
- Step 5: 텍스트 작성 중...
- Step 6: 이미지 생성 중...
- Step 7: PNG 렌더링 중...

## 완료 후
- output/ 폴더에 생성된 PNG 파일 목록을 보여주세요
- 마음에 안 드는 부분이 있으면 수정을 안내하세요
