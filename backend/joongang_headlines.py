"""중앙일보 홈페이지 '주요기사' 섹션에서 편집부 선정 기사 목록을 가져온다."""

import re
import urllib.request
from html import unescape

JOONGANG_HOME_URL = "https://www.joongang.co.kr/"
SOURCE_NAME = "중앙일보 주요기사"
SECTION_MARKER = '<strong class="title">주요기사</strong>'


def _clean_title(raw: str) -> str:
    text = re.sub(r"<[^>]+>", "", raw)
    return unescape(re.sub(r"\s+", " ", text)).strip()


def _extract_section(html: str) -> str:
    start = html.find(SECTION_MARKER)
    if start < 0:
        return ""
    rest = html[start + len(SECTION_MARKER) :]
    end = rest.find('<header class="title_wrap">')
    return rest[:end] if end > 0 else rest[:40000]


def fetch_headline_entries(limit: int = 100) -> list[dict]:
    """홈페이지 주요기사 블록에서 기사 제목·URL을 추출한다."""
    req = urllib.request.Request(
        JOONGANG_HOME_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; HanjulNews/1.0)"},
    )
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="replace")
    block = _extract_section(html)
    if not block:
        return []

    items: list[dict] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

    def add_item(url: str, title: str) -> None:
        if not title or url in seen_urls:
            return
        title_key = re.sub(r"\s+", "", title)
        if title_key in seen_titles:
            return
        seen_urls.add(url)
        seen_titles.add(title_key)
        items.append({
            "title": title,
            "url": url,
            "source": SOURCE_NAME,
            "feed_url": JOONGANG_HOME_URL,
            "rss_summary": "",
        })

    for match in re.finditer(
        r'<h2 class="headline">\s*<a href="(https://www\.joongang\.co\.kr/article/\d+)"[^>]*>(.*?)</a>',
        block,
        re.DOTALL,
    ):
        add_item(match.group(1).split("?")[0], _clean_title(match.group(2)))
        if len(items) >= limit:
            return items

    for match in re.finditer(
        r'<ul class="list_article">\s*<li><a href="(https://www\.joongang\.co\.kr/article/\d+)"[^>]*>(.*?)</a>',
        block,
        re.DOTALL,
    ):
        add_item(match.group(1).split("?")[0], _clean_title(match.group(2)))
        if len(items) >= limit:
            break

    return items
