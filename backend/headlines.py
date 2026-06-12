"""연합뉴스·중앙일보 등 편집부 선정 주요뉴스 목록을 통합한다."""

import re

from config import NEWS_SOURCE
from joongang_headlines import fetch_headline_entries as fetch_joongang_entries
from yna_headlines import fetch_headline_entries as fetch_yna_entries

HEADLINE_SOURCES = frozenset({"headlines", "yna_headlines", "joongang_headlines"})


def is_headline_source(source: str | None = None) -> bool:
    return (source or NEWS_SOURCE) in HEADLINE_SOURCES


def fetch_headline_entries(limit: int = 100) -> list[dict]:
    """설정된 소스에서 주요뉴스 목록을 합친다 (연합 → 중앙 순, 중복 제거)."""
    batches: list[list[dict]] = []

    if NEWS_SOURCE in ("headlines", "yna_headlines"):
        batches.append(fetch_yna_entries(limit=limit))
    if NEWS_SOURCE in ("headlines", "joongang_headlines"):
        batches.append(fetch_joongang_entries(limit=limit))

    merged: list[dict] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

    for batch in batches:
        for item in batch:
            title_key = re.sub(r"\s+", "", item["title"])
            if item["url"] in seen_urls or title_key in seen_titles:
                continue
            seen_urls.add(item["url"])
            seen_titles.add(title_key)
            merged.append(item)
            if len(merged) >= limit:
                return merged

    return merged
