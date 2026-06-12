"""API 서버: 뉴스 캐시 조회(GET)와 수집·요약 갱신(POST /refresh) 엔드포인트."""

import json
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from config import CACHE, CORS, MAX_ITEMS, OPENAI_API_KEY
from config import RSS_FEEDS
from fetcher import collect_rss_entries, fetch_articles
from summarizer import summarize_article

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=CORS, allow_methods=["*"], allow_headers=["*"])


def _refresh() -> dict:
    """RSS 수집 → LLM 요약 파이프라인을 실행하고, 결과를 캐시 파일에 저장한다."""
    if not OPENAI_API_KEY:
        raise HTTPException(503, "OPENAI_API_KEY is not set")
    articles = fetch_articles()
    if not articles:
        raise HTTPException(503, "No articles fetched")
    client = OpenAI(api_key=OPENAI_API_KEY)
    items = []
    for article in articles:
        if len(items) >= MAX_ITEMS:
            break
        try:
            item = summarize_article(client, article)
            if item:
                items.append(item)
        except Exception:
            continue
    if not items:
        raise HTTPException(503, "Summarization failed")
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
    items = data.get("items", [])
    return {"updated_at": data.get("updated_at"), "count": len(items), "items": items}


@app.post("/api/v1/news/refresh")
def post_refresh():
    """뉴스를 새로 수집·요약해 캐시를 갱신한다 (아침 배치·수동 실행용)."""
    return _refresh()
