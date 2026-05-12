"""네이버 검색 API: 자동완성·연관검색어·뉴스."""
import requests
from typing import Optional
from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
from utils.logger import get_logger

logger = get_logger(__name__)

_HEADERS = {
    "X-Naver-Client-Id": NAVER_CLIENT_ID,
    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
}
_TIMEOUT = 8


def is_configured() -> bool:
    return bool(NAVER_CLIENT_ID and NAVER_CLIENT_SECRET)


def search_news(keyword: str, display: int = 10) -> list[dict]:
    """네이버 뉴스 검색. [{title, link, description, pubDate}]."""
    if not is_configured():
        logger.warning("네이버 API 키 미설정 — news skip")
        return []
    try:
        r = requests.get(
            "https://openapi.naver.com/v1/search/news.json",
            headers=_HEADERS,
            params={"query": keyword, "display": display, "sort": "date"},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        return [{
            "title": _strip_tags(it.get("title", "")),
            "link": it.get("link", ""),
            "description": _strip_tags(it.get("description", "")),
            "pub_date": it.get("pubDate", ""),
        } for it in items]
    except Exception as e:
        logger.error(f"naver news 실패: {e}")
        return []


def search_blog(keyword: str, display: int = 10) -> list[dict]:
    """네이버 블로그 검색."""
    if not is_configured():
        return []
    try:
        r = requests.get(
            "https://openapi.naver.com/v1/search/blog.json",
            headers=_HEADERS,
            params={"query": keyword, "display": display, "sort": "sim"},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        return [{
            "title": _strip_tags(it.get("title", "")),
            "link": it.get("link", ""),
            "description": _strip_tags(it.get("description", "")),
            "blogger": it.get("bloggername", ""),
            "post_date": it.get("postdate", ""),
        } for it in items]
    except Exception as e:
        logger.error(f"naver blog 실패: {e}")
        return []


def _strip_tags(text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", text).replace("&quot;", '"').replace("&amp;", "&")
