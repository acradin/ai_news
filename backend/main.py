"""API 서버: 뉴스 캐시 조회(GET)와 수집·요약 갱신(POST /refresh) 엔드포인트."""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from config import CACHE, CATEGORY_ORDER, CORS, MAX_ITEMS, NEWS_TOPIC, OPENAI_API_KEY, RSS_FEEDS
from fetcher import collect_rss_entries, fetch_articles
from summarizer import summarize_article

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=CORS, allow_methods=["*"], allow_headers=["*"])


def _pick_one_per_category(items: list[dict]) -> list[dict]:
    """분야별 첫 기사 1건만 골라 고정 순서(경제→글로벌)로 반환한다."""
    by_category: dict[str, dict] = {}
    for item in items:
        category = item.get("category")
        if category in CATEGORY_ORDER and category not in by_category:
            by_category[category] = item
    return [by_category[c] for c in CATEGORY_ORDER if c in by_category]


def _refresh() -> dict:
    """RSS 수집 → LLM 요약 파이프라인을 실행하고, 결과를 캐시 파일에 저장한다."""
    if not OPENAI_API_KEY:
        raise HTTPException(503, "OPENAI_API_KEY is not set")
    articles = fetch_articles()
    if not articles:
        raise HTTPException(503, "No articles fetched")
    client = OpenAI(api_key=OPENAI_API_KEY)
    items: list[dict] = []
    items_by_category: dict[str, dict] = {}
    last_error = None
    target_count = MAX_ITEMS if NEWS_TOPIC == "politics" else len(CATEGORY_ORDER)
    for article in articles:
        if NEWS_TOPIC == "politics":
            if len(items) >= target_count:
                break
        elif len(items_by_category) >= target_count:
            break
        try:
            item = summarize_article(client, article)
            if not item:
                continue
            if NEWS_TOPIC == "politics":
                items.append(item)
            elif item["category"] not in items_by_category:
                items_by_category[item["category"]] = item
        except Exception as exc:
            last_error = exc
            logger.warning("summarize failed for %s: %s", article.get("url"), exc)
            continue
    if NEWS_TOPIC != "politics":
        items = [items_by_category[c] for c in CATEGORY_ORDER if c in items_by_category]
    if not items:
        detail = f"Summarization failed: {last_error}" if last_error else "Summarization failed"
        raise HTTPException(503, detail)
    updated_at = datetime.now(timezone.utc).isoformat()
    CACHE.write_text(json.dumps({"updated_at": updated_at, "items": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "count": len(items), "updated_at": updated_at}


@app.get("/health")
def health():
    """서버가 살아 있는지 확인하는 헬스체크 엔드포인트."""
    return {"status": "ok"}


@app.get("/api/v1/feeds")
def get_feeds():
    """등록된 RSS 목록과 피드별 수집 결과를 반환한다 (본문 추출·LLM 없음, 동작 확인용)."""
    result = collect_rss_entries()
    return {
        "configured_feeds": len(RSS_FEEDS),
        "total_entries": result["total_entries"],
        "feeds": result["feeds"],
        "samples": [
            {"title": e["title"], "source": e["source"], "url": e["url"]}
            for e in result["entries"][:10]
        ],
    }


@app.get("/api/v1/news")
def get_news():
    """캐시에 저장된 오늘의 뉴스 목록을 조회한다 (수집/요약은 하지 않음)."""
    if not CACHE.exists():
        return {"updated_at": None, "count": 0, "items": []}
    data = json.loads(CACHE.read_text(encoding="utf-8"))
    cached = data.get("items", [])
    if NEWS_TOPIC == "politics":
        items = cached[:MAX_ITEMS]
    else:
        items = _pick_one_per_category(cached)
    return {"updated_at": data.get("updated_at"), "count": len(items), "items": items}


@app.post("/api/v1/news/refresh")
def post_refresh():
    """뉴스를 새로 수집·요약해 캐시를 갱신한다 (아침 배치·수동 실행용)."""
    return _refresh()
