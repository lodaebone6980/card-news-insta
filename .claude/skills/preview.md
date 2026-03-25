---
name: preview
description: 마지막으로 생성된 카드뉴스를 미리보기합니다.
---

# /preview — 카드뉴스 미리보기

## 동작
1. output/ 디렉토리에서 가장 최근 세션 폴더를 찾기
2. session_data.json을 읽어서 정보 표시
3. 생성된 PNG 파일들을 Read 도구로 보여주기

## 표시 정보
- 세션 시간
- 선정된 주제
- 앵글
- 각 슬라이드 요약 (제목 + 유형)
- PNG 파일 목록 및 이미지 미리보기

## 수정 안내
미리보기 후 사용자에게 수정 가능한 옵션을 안내:
- "주제가 마음에 안 들면 → 다시 `/generate` 실행"
- "톤이 이상하면 → brand.md의 톤앤매너 수정 후 재실행"
- "이미지가 별로면 → prompts/image_generator.md의 보강 규칙 수정"
- "디자인 수정 → templates/ 폴더의 HTML 수정"
