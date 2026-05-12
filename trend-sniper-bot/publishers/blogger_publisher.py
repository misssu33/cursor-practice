"""Blogger 자동 발행."""
from publishers.base import PublishResult
from oauth.blogger_oauth import get_credentials
from config import BLOGGER_BLOG_ID
from utils.logger import get_logger

logger = get_logger(__name__)


def publish(user_id: int, title: str, body_md: str, labels: list[str] | None = None) -> PublishResult:
    if not BLOGGER_BLOG_ID:
        return PublishResult(ok=False, error=".env에 BLOGGER_BLOG_ID 미설정")

    creds = get_credentials(user_id)
    if not creds:
        return PublishResult(ok=False, error="/connect blogger 로 먼저 인증해 주세요")

    try:
        import markdown as md
        from googleapiclient.discovery import build

        html = md.markdown(
            body_md,
            extensions=["fenced_code", "tables", "toc", "nl2br"],
        )
        service = build("blogger", "v3", credentials=creds, cache_discovery=False)
        post_body = {
            "kind": "blogger#post",
            "title": title,
            "content": html,
        }
        if labels:
            post_body["labels"] = labels

        res = service.posts().insert(
            blogId=BLOGGER_BLOG_ID,
            body=post_body,
            isDraft=False,
        ).execute()

        url = res.get("url")
        logger.info(f"Blogger 발행: {url}")
        return PublishResult(ok=True, url=url, raw=res)
    except Exception as e:
        logger.error(f"Blogger 발행 실패: {e}", exc_info=True)
        return PublishResult(ok=False, error=str(e))
