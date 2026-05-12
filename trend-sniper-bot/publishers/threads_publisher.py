"""Threads 자동 발행 — 5포스트 순차 + 리플라이 체인."""
import time
import requests
from publishers.base import PublishResult
from oauth.threads_oauth import is_configured as threads_configured
from config import THREADS_ACCESS_TOKEN, THREADS_USER_ID, MAX_RETRY
from utils.logger import get_logger

logger = get_logger(__name__)
API = "https://graph.threads.net/v1.0"


def _create_container(text: str, reply_to_id: str | None = None) -> str | None:
    params = {
        "media_type": "TEXT",
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN,
    }
    if reply_to_id:
        params["reply_to_id"] = reply_to_id
    try:
        r = requests.post(f"{API}/{THREADS_USER_ID}/threads", data=params, timeout=15)
        r.raise_for_status()
        return r.json().get("id")
    except Exception as e:
        logger.error(f"threads container 실패: {e}")
        return None


def _publish_container(creation_id: str) -> str | None:
    try:
        r = requests.post(
            f"{API}/{THREADS_USER_ID}/threads_publish",
            data={"creation_id": creation_id, "access_token": THREADS_ACCESS_TOKEN},
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("id")
    except Exception as e:
        logger.error(f"threads publish 실패: {e}")
        return None


def publish(body: str) -> PublishResult:
    """본문(--- 구분자 분할) → 5포스트 발행 + 리플라이 체인."""
    if not threads_configured():
        return PublishResult(ok=False, error="Threads 미설정")

    posts = [p.strip() for p in body.split("\n---\n") if p.strip()]
    if not posts:
        return PublishResult(ok=False, error="발행할 포스트 없음")

    first_post_id = None
    parent_id = None

    for i, post in enumerate(posts, 1):
        # 컨테이너 생성 (지수 백오프 재시도)
        creation_id = None
        for attempt in range(MAX_RETRY):
            creation_id = _create_container(post, reply_to_id=parent_id)
            if creation_id:
                break
            time.sleep(2 ** attempt)
        if not creation_id:
            return PublishResult(ok=False, error=f"포스트 {i} 컨테이너 실패")

        # Threads는 컨테이너 생성 후 잠시 대기 권장.
        time.sleep(2)
        published_id = None
        for attempt in range(MAX_RETRY):
            published_id = _publish_container(creation_id)
            if published_id:
                break
            time.sleep(2 ** attempt)
        if not published_id:
            return PublishResult(ok=False, error=f"포스트 {i} 발행 실패")

        logger.info(f"Threads {i}/{len(posts)} 발행: id={published_id}")
        if i == 1:
            first_post_id = published_id
        parent_id = published_id

    url = f"https://www.threads.net/@me/post/{first_post_id}" if first_post_id else None
    return PublishResult(ok=True, url=url, raw={"posts_published": len(posts)})
