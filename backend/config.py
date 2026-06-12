"""환경 변수(.env)와 공통 설정 — API 키, RSS URL, 캐시 경로, LLM 프롬프트."""

import os
from pathlib import Path

from dotenv import load_dotenv

from feeds import DEFAULT_RSS_FEEDS

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
MAX_ITEMS = int(os.getenv("NEWS_MAX_ITEMS", "5"))
FETCH_BODY_LIMIT = int(os.getenv("FETCH_BODY_LIMIT", "30"))


def _load_rss_feeds() -> list[dict]:
    raw = os.getenv("RSS_FEEDS", "").strip()
    if not raw:
        return DEFAULT_RSS_FEEDS
    feeds: list[dict] = []
    for item in raw.split(","):
        url = item.strip()
        if url:
            feeds.append({"name": url, "url": url})
    return feeds


RSS_FEEDS = _load_rss_feeds()
CACHE = Path(os.getenv("NEWS_CACHE_PATH", "./data/news_cache.json"))
CORS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3456").split(",") if o.strip()]

CATEGORIES = {"AI", "경제", "정책", "사회", "글로벌"}

PROMPT = (
    "fact-only 뉴스 편집자. 한국어 한 문장, 120자 이내. 의견·추측·자극적 표현 금지. "
    'JSON만: {"summary":"...", "category":"AI|경제|정책|사회|글로벌"}'
)

CACHE.parent.mkdir(parents=True, exist_ok=True)
