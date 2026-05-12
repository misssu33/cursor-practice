"""YouTube Data API v3: 인기 영상 검색."""
import requests
from config import YOUTUBE_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)
_TIMEOUT = 8


def is_configured() -> bool:
    return bool(YOUTUBE_API_KEY)


def search_videos(keyword: str, max_results: int = 10) -> list[dict]:
    """키워드 기준 최근 1개월 조회수 상위 영상."""
    if not is_configured():
        logger.warning("YouTube API 키 미설정 — skip")
        return []
    try:
        # 1단계: 검색
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet", "q": keyword, "type": "video",
                "order": "viewCount", "maxResults": max_results,
                "relevanceLanguage": "ko", "regionCode": "KR",
                "key": YOUTUBE_API_KEY,
            },
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        video_ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]
        if not video_ids:
            return []

        # 2단계: 통계 보강
        r2 = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet,statistics",
                "id": ",".join(video_ids),
                "key": YOUTUBE_API_KEY,
            },
            timeout=_TIMEOUT,
        )
        r2.raise_for_status()
        videos = r2.json().get("items", [])
        return [{
            "video_id": v["id"],
            "title": v["snippet"]["title"],
            "channel": v["snippet"]["channelTitle"],
            "published_at": v["snippet"]["publishedAt"],
            "url": f"https://www.youtube.com/watch?v={v['id']}",
            "view_count": int(v.get("statistics", {}).get("viewCount", 0)),
            "like_count": int(v.get("statistics", {}).get("likeCount", 0)),
            "comment_count": int(v.get("statistics", {}).get("commentCount", 0)),
        } for v in videos]
    except Exception as e:
        logger.error(f"youtube 실패: {e}")
        return []
