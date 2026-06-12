"""환경 변수(.env)와 공통 설정 — API 키, RSS URL, 캐시 경로, LLM 프롬프트."""

import os
from pathlib import Path

from dotenv import load_dotenv

from feeds import DEFAULT_RSS_FEEDS, POLITICS_RSS_FEEDS

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
MAX_ITEMS = int(os.getenv("NEWS_MAX_ITEMS", "5"))
FETCH_BODY_LIMIT = int(os.getenv("FETCH_BODY_LIMIT", "30"))
MIN_IMPORTANCE_SCORE = int(os.getenv("MIN_IMPORTANCE_SCORE", "7"))
NEWS_SOURCE = os.getenv("NEWS_SOURCE", "headlines").strip().lower()
NEWS_TOPIC = os.getenv("NEWS_TOPIC", "politics").strip().lower()


def _load_rss_feeds() -> list[dict]:
    if NEWS_SOURCE in ("headlines", "yna_headlines", "joongang_headlines"):
        feeds: list[dict] = []
        if NEWS_SOURCE in ("headlines", "yna_headlines"):
            feeds.append({"name": "연합뉴스 주요뉴스", "url": "https://www.yna.co.kr/theme/headlines-history"})
        if NEWS_SOURCE in ("headlines", "joongang_headlines"):
            feeds.append({"name": "중앙일보 주요기사", "url": "https://www.joongang.co.kr/"})
        return feeds
    raw = os.getenv("RSS_FEEDS", "").strip()
    if raw:
        feeds: list[dict] = []
        for item in raw.split(","):
            url = item.strip()
            if url:
                feeds.append({"name": url, "url": url})
        return feeds
    if NEWS_TOPIC == "politics":
        return POLITICS_RSS_FEEDS
    seen: set[str] = set()
    feeds: list[dict] = []
    for feed in POLITICS_RSS_FEEDS + DEFAULT_RSS_FEEDS:
        if feed["url"] not in seen:
            seen.add(feed["url"])
            feeds.append(feed)
    return feeds


_SUMMARY_STYLE = (
    "한 줄 요약은 반드시 명사형으로 종결. "
    "'~했다·~이다·~합니다·~예정이다' 등 서술형·평서형 종결 금지. "
    "예: '한성숙 총리 후보자, 청년 직원과 오찬' / '코스피, 전일 대비 상승 마감'"
)

_CATEGORY_RULES = (
    "category는 기사 내용에 맞게 정확히 하나만 선택. "
    "정치=대통령·총리·국회·정당·선거·외교·국방·사법(정치인·정치 사건). "
    "경제=주식·금리·환율·기업 실적·무역·부동산 시장. "
    "정책=법안·규제·정부 정책·예산·복지·노동 제도. "
    "사회=사건·사고·범죄·교육·노동 현장·지역·문화·스포츠. "
    "글로벌=해외 정부·국제 분쟁·외국 기업·국제기구."
)

_IMPORTANCE_RULES = (
    "중요도 score(1~10)와 important를 함께 판단. important는 전국적·사회적 영향이 큰 기사만 true, score 7 이상만 채택. "
    "important=false(제외): 시·군·구·대학·기업 홍보, 세미나·공모전·개강·축제·시상·체험·참관·훈련 행사, "
    "지역 행사·기념·참배·유해발굴 등 단순 보도자료. "
    "important=true(포함): 대통령·총리·국회·법안·예산·선거, 금리·환율·코스피·주요 경제정책, "
    "주요 외교·안보·국제회담, 전국적 사회 이슈."
)

if NEWS_TOPIC == "politics":
    CATEGORIES = {"정치"}
    CATEGORY_ORDER = ["정치"]
    PROMPT = (
        "fact-only 정치 뉴스 편집자. 국회·정부·선거·외교 등 정치 기사만 다룬다. "
        "한국어 한 줄, 120자 이내. 의견·추측·자극적 표현 금지. "
        f"{_SUMMARY_STYLE} {_CATEGORY_RULES} {_IMPORTANCE_RULES} "
        'JSON만: {"important": true, "score": 8, "summary": "...", "category": "정치"}'
    )
else:
    CATEGORIES = {"정치", "경제", "정책", "사회", "글로벌"}
    CATEGORY_ORDER = ["정치", "경제", "정책", "사회", "글로벌"]
    _HEADLINE_JSON = '{"summary": "...", "category": "정치|경제|정책|사회|글로벌"}'
    _RSS_JSON = '{"important": true, "score": 8, "summary": "...", "category": "정치|경제|정책|사회|글로벌"}'
    PROMPT = (
        "fact-only 뉴스 편집자. 한국어 한 줄, 120자 이내. 의견·추측·자극적 표현 금지. "
        f"{_SUMMARY_STYLE} {_CATEGORY_RULES} "
        + ("" if NEWS_SOURCE in ("headlines", "yna_headlines", "joongang_headlines") else _IMPORTANCE_RULES + " ")
        + f"JSON만: {_HEADLINE_JSON if NEWS_SOURCE in ('headlines', 'yna_headlines', 'joongang_headlines') else _RSS_JSON}"
    )

RSS_FEEDS = _load_rss_feeds()
CACHE = Path(os.getenv("NEWS_CACHE_PATH", "./data/news_cache.json"))
CORS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3456").split(",") if o.strip()]

CACHE.parent.mkdir(parents=True, exist_ok=True)
