"""Step 1: RSS 크롤링 — 24시간 이내 헤드라인 수집"""

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import httpx

from .config import parse_news_sources


async def fetch_feed(client: httpx.AsyncClient, url: str) -> list[dict]:
    """단일 RSS 피드에서 헤드라인 추출"""
    headlines = []
    try:
        resp = await client.get(url, timeout=15.0, follow_redirects=True)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)

        # RSS 2.0
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "")

            if title:
                headlines.append({
                    "title": title,
                    "url": link,
                    "pub_date": pub_date,
                    "source": url,
                })

        # Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns):
            title = entry.findtext("atom:title", "", ns).strip()
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            updated = entry.findtext("atom:updated", "", ns)

            if title:
                headlines.append({
                    "title": title,
                    "url": link,
                    "pub_date": updated,
                    "source": url,
                })

    except Exception as e:
        print(f"  [경고] 피드 실패: {url} — {e}")

    return headlines


def is_within_hours(pub_date_str: str, hours: int = 48) -> bool:
    """발행일이 N시간 이내인지 확인 (파싱 실패 시 True 반환)"""
    if not pub_date_str:
        return True
    try:
        dt = parsedate_to_datetime(pub_date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return dt >= cutoff
    except Exception:
        try:
            # ISO 8601 형식 시도
            dt = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            return dt >= cutoff
        except Exception:
            return True


async def crawl() -> list[dict]:
    """모든 RSS 소스에서 최근 헤드라인 수집"""
    urls = parse_news_sources()
    print(f"[Crawler] {len(urls)}개 RSS 소스 크롤링 시작...")

    async with httpx.AsyncClient(
        headers={"User-Agent": "CardNewsBot/1.0"},
    ) as client:
        tasks = [fetch_feed(client, url) for url in urls]
        results = await asyncio.gather(*tasks)

    all_headlines = []
    for headlines in results:
        for h in headlines:
            if is_within_hours(h["pub_date"], hours=48):
                all_headlines.append(h)

    # 중복 제거 (제목 기준)
    seen = set()
    unique = []
    for h in all_headlines:
        if h["title"] not in seen:
            seen.add(h["title"])
            unique.append(h)

    print(f"[Crawler] 총 {len(unique)}개 헤드라인 수집 완료")
    return unique


def run() -> list[dict]:
    return asyncio.run(crawl())
