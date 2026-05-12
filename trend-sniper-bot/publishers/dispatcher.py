"""채널별 발행 디스패처 — auto/semi/manual 자동 분기."""
from datetime import datetime, timezone
from publishers.base import PublishResult
from publishers import threads_publisher, blogger_publisher, instagram_publisher
from channels.base import get_channel, PublishMode
from storage import get_session
from storage.models import ChannelContent
from utils.logger import get_logger

logger = get_logger(__name__)


def _now_naive_utc() -> datetime:
    """모델의 DateTime 컬럼이 naive 라 일관성 유지를 위해 UTC naive 로 반환."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_content(content_id: int) -> ChannelContent | None:
    with get_session() as session:
        return session.get(ChannelContent, content_id)


def dispatch(content_id: int, user_id: int) -> PublishResult:
    """채널 메타에 따라 자동 라우팅. manual은 발행 건너뛰고 안내만."""
    with get_session() as session:
        content = session.get(ChannelContent, content_id)
        if not content:
            return PublishResult(ok=False, error=f"콘텐츠 #{content_id} 없음")
        channel_key = content.channel
        body = content.body
        # adsense 본문에서 제목 추출 (첫 줄 "# 제목")
        extra_title = None
        if channel_key == "adsense":
            first_line = body.split("\n", 1)[0]
            if first_line.startswith("# "):
                extra_title = first_line[2:].strip()

    spec = get_channel(channel_key)
    logger.info(f"dispatch: channel={channel_key}, mode={spec.publish_mode.value}, content={content_id}")

    if spec.publish_mode == PublishMode.AUTO:
        if channel_key == "threads":
            result = threads_publisher.publish(body)
        elif channel_key == "adsense":
            result = blogger_publisher.publish(
                user_id=user_id,
                title=extra_title or "제목 없음",
                body_md=body,
            )
        else:
            return PublishResult(ok=False, error=f"자동 발행 미지원: {channel_key}")

    elif spec.publish_mode == PublishMode.SEMI_AUTO:
        # 캡션 = 본문 중 === CAPTION === 이후
        caption = body
        if "=== CAPTION ===" in body:
            caption = body.split("=== CAPTION ===", 1)[1].strip()
        caption = caption[:2200]
        result = instagram_publisher.publish(content_id, caption)

    else:
        # 수동 (네이버·링크드인) — 봇은 본문만 안내, 사용자가 직접 발행.
        return PublishResult(
            ok=True,
            url=None,
            raw={"manual": True, "channel": channel_key},
            error=None,
        )

    # 결과 DB 반영
    if result.ok:
        with get_session() as session:
            row = session.get(ChannelContent, content_id)
            if row:
                row.status = "published"
                row.published_url = result.url or ""
                row.published_at = _now_naive_utc()
    else:
        with get_session() as session:
            row = session.get(ChannelContent, content_id)
            if row:
                row.status = "failed"

    return result
