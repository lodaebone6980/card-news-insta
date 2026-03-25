"""AI 카드뉴스 자동생성기 — 메인 파이프라인"""

import json
import sys
from datetime import datetime
from pathlib import Path

from pipeline.config import GEMINI_API_KEY, OUTPUT_DIR


def main():
    # API 키 확인
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY 환경변수를 설정해주세요.")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        sys.exit(1)

    # 세션명 (타임스탬프)
    session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n{'='*60}")
    print(f"  AI 카드뉴스 자동생성기")
    print(f"  세션: {session_name}")
    print(f"{'='*60}\n")

    # Step 1: RSS 크롤링
    print("━" * 40)
    print("Step 1/7: RSS 크롤링")
    print("━" * 40)
    from pipeline.crawler import run as crawl
    headlines = crawl()

    if not headlines:
        print("[오류] 수집된 헤드라인이 없습니다. news_sources.txt를 확인하세요.")
        sys.exit(1)

    # Step 2: 주제 선정
    print(f"\n{'━'*40}")
    print("Step 2/7: 주제 선정 (Gemini Flash)")
    print("━" * 40)
    from pipeline.topic_selector import select_topic
    topic = select_topic(headlines)

    # Step 3: 기획안 작성
    print(f"\n{'━'*40}")
    print("Step 3/7: 기획안 작성 (Gemini Flash)")
    print("━" * 40)
    from pipeline.editor import create_plan
    plan = create_plan(topic)

    # Step 4: 리서치
    print(f"\n{'━'*40}")
    print("Step 4/7: 팩트 리서치 (Gemini Pro + Search)")
    print("━" * 40)
    from pipeline.researcher import research
    research_data = research(plan)

    # Step 5: 텍스트 작성
    print(f"\n{'━'*40}")
    print("Step 5/7: 텍스트 작성 (Gemini Pro)")
    print("━" * 40)
    from pipeline.writer import write
    writer_output = write(plan, research_data)

    # Step 6: 이미지 생성
    print(f"\n{'━'*40}")
    print("Step 6/7: AI 이미지 생성 (Gemini)")
    print("━" * 40)
    from pipeline.image_generator import generate_images
    image_paths = generate_images(writer_output, session_name)

    # Step 7: PNG 렌더링
    print(f"\n{'━'*40}")
    print("Step 7/7: HTML → PNG 렌더링")
    print("━" * 40)
    from pipeline.renderer import render_all
    png_paths = render_all(writer_output, image_paths, session_name)

    # 중간 데이터 저장 (디버깅/재사용)
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
    data_path = session_dir / "session_data.json"
    data_path.write_text(json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 완료
    print(f"\n{'='*60}")
    print(f"  카드뉴스 생성 완료!")
    print(f"  출력 경로: {session_dir}")
    print(f"  PNG 파일: {len(png_paths)}장")
    for p in png_paths:
        print(f"    - {Path(p).name}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
