import feedparser


def fetch_latest_entries(url: str, limit: int = 3):
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:limit]:
        items.append({
            "title": entry.title,
            "link": entry.link,
            "summary": getattr(entry, "summary", ""),
            "published": getattr(entry, "published", ""),
        })
    return items
