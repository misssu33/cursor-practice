"""RSS 피드 수집 (한국 주요 매체)."""
import feedparser
from utils.logger import get_logger

logger = get_logger(__name__)

# 한국 주요 매체 RSS (변경 가능성 있음 — 동작 안 하면 update_at 갱신 시 무시)
DEFAULT_FEEDS = [
    ("연합뉴스", "https://www.yna.co.kr/rss/news.xml"),
    ("한국경제", "https://www.hankyung.com/feed/all-news"),
    ("ZDNet Korea", "https://feeds.feedburner.com/zdkorea"),
    ("Bloter", "https://www.bloter.net/feed"),
]


def collect(keyword: str, feeds: list[tuple[str, str]] | None = None, limit_per_feed: int = 5) -> list[dict]:
    """피드에서 키워드 포함 항목 수집."""
    feeds = feeds or DEFAULT_FEEDS
    results: list[dict] = []
    for name, url in feeds:
        try:
            d = feedparser.parse(url)
            cnt = 0
            for entry in d.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                if keyword.lower() not in (title + summary).lower():
                    continue
                results.append({
                    "source": name,
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": summary[:200],
                    "published": entry.get("published", ""),
                })
                cnt += 1
                if cnt >= limit_per_feed:
                    break
        except Exception as e:
            logger.warning(f"RSS {name} 실패: {e}")
    return results
