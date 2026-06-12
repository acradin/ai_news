"""뉴스 수집: 여러 RSS 피드 파싱 + 기사 URL에서 본문 텍스트 추출."""

import trafilatura
import feedparser

from config import FETCH_BODY_LIMIT, RSS_FEEDS


def extract_body(url: str, fallback: str = "") -> str:
    """기사 URL에서 본문 텍스트를 추출한다. 실패 시 RSS 요약(fallback)을 쓴다."""
    html = trafilatura.fetch_url(url)
    if not html:
        return fallback.strip()[:8000]
    text = trafilatura.extract(html, favor_precision=True) or fallback
    return text.strip()[:8000]


def collect_rss_entries() -> dict:
    """등록된 모든 RSS 피드를 파싱해 기사 메타데이터를 모은다 (본문 추출 없음)."""
    entries: list[dict] = []
    seen_urls: set[str] = set()
    feed_results: list[dict] = []

    for feed in RSS_FEEDS:
        name = feed["name"]
        url = feed["url"]
        parsed = feedparser.parse(url)
        error = str(parsed.bozo_exception) if parsed.bozo else None
        feed_entries: list[dict] = []

        for entry in parsed.entries:
            article_url = (entry.get("link") or "").strip()
            title = (entry.get("title") or "").strip()
            if not article_url or not title or article_url in seen_urls:
                continue

            seen_urls.add(article_url)
            item = {
                "title": title,
                "url": article_url,
                "source": name,
                "feed_url": url,
                "rss_summary": entry.get("summary") or entry.get("description") or "",
            }
            feed_entries.append(item)
            entries.append(item)

        feed_results.append({
            "name": name,
            "url": url,
            "ok": bool(parsed.entries) and not parsed.bozo,
            "entry_count": len(feed_entries),
            "error": error,
        })

    return {
        "feed_count": len(RSS_FEEDS),
        "total_entries": len(entries),
        "feeds": feed_results,
        "entries": entries,
    }


def fetch_articles() -> list[dict]:
    """모든 RSS에서 모은 기사에 본문을 붙여 LLM 처리용 리스트로 반환한다."""
    collected = collect_rss_entries()
    articles: list[dict] = []

    for entry in collected["entries"]:
        if len(articles) >= FETCH_BODY_LIMIT:
            break

        body = extract_body(entry["url"], entry["rss_summary"])
        if len(body) < 80:
            continue

        articles.append({
            "title": entry["title"],
            "url": entry["url"],
            "source": entry["source"],
            "feed_url": entry["feed_url"],
            "body": body,
        })

    return articles
