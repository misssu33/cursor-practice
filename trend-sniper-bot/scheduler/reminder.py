"""APScheduler 기반 발행 5분 전 알림 + 자동 발행 트리거.

봇 프로세스 메모리에만 잡이 저장되므로, 재시작 시 잡은 사라진다.
영속화가 필요하면 SQLAlchemyJobStore 로 바꿔야 하지만 현 범위 밖.
"""
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from telegram.ext import Application

from config import TIMEZONE, REMINDER_BEFORE_MIN
from storage import get_session
from storage.models import Schedule, ChannelContent
from channels.base import get_channel, PublishMode
from publishers.dispatcher import dispatch
from utils.logger import get_logger

logger = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    return _scheduler


def start():
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        logger.info(f"⏰ Scheduler 시작 (tz={TIMEZONE})")


def add_schedule(
    app: Application,
    schedule_id: int,
    user_id: int,
    chat_id: int,
):
    """스케줄 1건 등록 — 5분 전 알림 + 정시 자동발행."""
    with get_session() as session:
        sch = session.get(Schedule, schedule_id)
        if not sch:
            return
        publish_at = sch.publish_at
        channel = sch.channel
        content_row = (
            session.query(ChannelContent)
            .filter_by(project_id=sch.project_id, channel=channel)
            .first()
        )
        content_id = content_row.id if content_row else None

    if not content_id:
        return

    sched = get_scheduler()
    spec = get_channel(channel)

    # 5분 전 알림
    remind_at = publish_at - timedelta(minutes=REMINDER_BEFORE_MIN)
    if remind_at > datetime.now():
        sched.add_job(
            _remind_job,
            trigger=DateTrigger(run_date=remind_at),
            args=[app, chat_id, schedule_id, channel, publish_at],
            id=f"remind_{schedule_id}",
            replace_existing=True,
        )

    # 정시 자동 발행 (auto/semi만)
    if spec.publish_mode in (PublishMode.AUTO, PublishMode.SEMI_AUTO):
        sched.add_job(
            _publish_job,
            trigger=DateTrigger(run_date=publish_at),
            args=[app, chat_id, user_id, schedule_id, content_id, channel],
            id=f"pub_{schedule_id}",
            replace_existing=True,
        )

    logger.info(f"스케줄 등록: id={schedule_id}, channel={channel}, at={publish_at}")


async def _remind_job(app: Application, chat_id: int, schedule_id: int, channel: str, publish_at: datetime):
    spec = get_channel(channel)
    mode = spec.publish_mode.value
    text = (
        f"⏰ *5분 후 발행 예정*\n\n"
        f"채널: {channel}\n"
        f"시간: {publish_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"모드: {mode}\n\n"
    )
    if mode == "manual":
        text += "수동 채널입니다. 직접 발행 후 /publish 메뉴의 ✅ 버튼으로 알려주세요."
    elif mode == "semi":
        text += "반자동 채널 — 정시에 자동 시도됩니다."
    else:
        text += "자동 채널 — 정시에 자동 발행됩니다."

    try:
        await app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        with get_session() as session:
            sch = session.get(Schedule, schedule_id)
            if sch:
                sch.reminded = True
    except Exception as e:
        logger.error(f"remind_job 실패: {e}")


async def _publish_job(
    app: Application, chat_id: int, user_id: int,
    schedule_id: int, content_id: int, channel: str,
):
    logger.info(f"자동 발행 실행: schedule={schedule_id}, content={content_id}, channel={channel}")
    try:
        result = dispatch(content_id, user_id)
        with get_session() as session:
            sch = session.get(Schedule, schedule_id)
            if sch:
                sch.executed = True
                sch.result = f"{'OK' if result.ok else 'FAIL'}: {result.url or result.error}"

        if result.ok:
            msg = f"✅ *{channel}* 발행 완료\n🔗 {result.url or '(URL 없음)'}"
        else:
            msg = f"❌ *{channel}* 발행 실패\n오류: {result.error}"
        await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"publish_job 예외: {e}", exc_info=True)
        await app.bot.send_message(chat_id=chat_id, text=f"❌ 발행 중 예외: {e}")
