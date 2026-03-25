# Image Generator Guide

Writer가 만든 image_prompt로 Gemini가 AI 배경 이미지를 생성합니다.

## 모델 정보
- 모델명: `gemini-2.5-flash-image` (변경될 수 있음)
- 에러 발생 시 Google AI Studio에서 최신 이미지 생성 모델명 확인

## 이미지 프롬프트 보강 규칙
image_prompt 끝에 항상 다음을 추가:
```
Shot with 85mm lens, f/2.0, ISO 200, shallow depth of field.
Natural soft lighting creating gentle highlights and subtle shadows.
High detail, unretouched quality.
Avoid: blurry, distorted, text, watermark, logo, infographic, chart, graph, diagram, abstract gradient
```

## 생성 설정
- 출력 사이즈: 1080x1350 비율에 맞게
- 슬라이드별 2~3초 간격 (rate limit 방지)
- 최대 재시도: 3회

## 실패 대응
1. 첫 번째 실패: 프롬프트를 더 구체적으로 수정 후 재시도
2. 두 번째 실패: 추상적 표현 모두 제거 후 재시도
3. 세 번째 실패: 단순한 배경 컬러/그라데이션으로 대체

## 슬라이드별 이미지 팁
| 슬라이드 | 팁 |
|----------|-----|
| 표지 | 강렬한 단일 오브제, 어두운 배경 추천 |
| 본문 | 좌측 또는 우측에 텍스트 공간 확보 |
| 마지막 | 브랜드 컬러 톤의 심플한 배경 |
