"""뉴스 요약: OpenAI로 기사 본문을 fact-only 한 줄 + 카테고리로 변환."""

import json
from datetime import datetime

from openai import OpenAI

from config import CATEGORIES, MIN_IMPORTANCE_SCORE, OPENAI_MODEL, PROMPT
from headlines import is_headline_source


def summarize_article(client: OpenAI, article: dict) -> dict | None:
    """OpenAI로 기사를 fact-only 한 줄 요약하고, 프론트용 뉴스 카드 dict를 만든다."""
    res = client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"제목: {article['title']}\n출처: {article['source']}\n본문:\n{article['body']}"},
        ],
    )
    data = json.loads(res.choices[0].message.content or "{}")
    summary = (data.get("summary") or "").strip()
    if not summary:
        return None

    try:
        score = int(data.get("score") or 0)
    except (TypeError, ValueError):
        score = 0

    if not is_headline_source():
        if not bool(data.get("important")) or score < MIN_IMPORTANCE_SCORE:
            return None

    category = (data.get("category") or "").strip()
    if category not in CATEGORIES:
        return None

    now = datetime.now()
    return {
        "id": str(abs(hash(article["url"])))[:12],
        "category": category,
        "published_at": now.strftime("%Y-%m-%d"),
        "date_label": f"{now.month}월 {now.day}일",
        "summary": summary,
        "source_name": article["source"],
        "source_url": article["url"],
        "importance_score": score,
    }
