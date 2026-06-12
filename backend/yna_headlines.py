"""연합뉴스 테마 '주요뉴스' 페이지에서 편집부 선정 기사 목록을 가져온다."""

import re
import urllib.request
from html import unescape
from urllib.parse import parse_qs, urlparse

YNA_HEADLINES_URL = "https://www.yna.co.kr/theme/headlines-history"
SOURCE_NAME = "연합뉴스 주요뉴스"

SECTION_TO_CATEGORY = {
    "politics": "정치",
    "northkorea": "정치",
    "economy": "경제",
    "market": "경제",
    "industry": "경제",
    "society": "사회",
    "international": "글로벌",
}


def _normalize_url(url: str) -> str:
    return url.split("?")[0]


def _hint_category(url: str) -> str | None:
    section = (parse_qs(urlparse(url).query).get("section") or [""])[0]
    key = section.split("/")[0] if section else ""
    return SECTION_TO_CATEGORY.get(key)


def fetch_headline_entries(limit: int = 100) -> list[dict]:
    """주요뉴스 페이지 HTML에서 기사 제목·URL을 추출한다 (편집부 선정 순서 유지)."""
    req = urllib.request.Request(
        YNA_HEADLINES_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; HanjulNews/1.0)"},
    )
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8")

    items: list[dict] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

    pattern = re.compile(
        r'<a href="(https://www\.yna\.co\.kr/view/AKR[^"]+)" class="tit-news">\s*'
        r'<span class="title01">([^<]+)</span>',
        re.DOTALL,
    )
    for match in pattern.finditer(html):
        raw_url = match.group(1)
        url = _normalize_url(raw_url)
        title = unescape(match.group(2).strip())
        title_key = re.sub(r"\s+", "", title)
        if not title or url in seen_urls or title_key in seen_titles:
            continue

        seen_urls.add(url)
        seen_titles.add(title_key)
        items.append({
            "title": title,
            "url": url,
            "source": SOURCE_NAME,
            "feed_url": YNA_HEADLINES_URL,
            "hint_category": _hint_category(raw_url),
            "rss_summary": "",
        })
        if len(items) >= limit:
            break

    return items
