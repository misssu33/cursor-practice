"""발행 핸들러 — /publish, 수동 채널 ✅완료 버튼, 일정 등록."""
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from channels.base import get_channel, PublishMode
from publishers.dispatcher import dispatch
from scheduler import add_schedule
from storage import get_session
from storage.models import Project, ChannelContent, Schedule
from utils import require_auth, get_logger

logger = get_logger(__name__)


def _now_naive_utc() -> datetime:
    """models 의 DateTime 컬럼이 naive 라 일관성 유지를 위해 UTC naive 반환."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@require_auth
async def cmd_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/publish — 현재 프로젝트 모든 ready 채널 발행 (즉시)."""
    project_id = context.user_data.get("project_id")
    if not project_id:
        await update.message.reply_text("⚠️ 진행 중인 프로젝트가 없습니다.")
        return

    user_id = update.effective_user.id

    with get_session() as session:
        contents = (
            session.query(ChannelContent)
            .filter_by(project_id=project_id, status="ready")
            .all()
        )
        targets = [(c.id, c.channel) for c in contents]

    if not targets:
        await update.message.reply_text("⚠️ 발행 가능한 채널이 없습니다. (SEO 합격 채널 없음)")
        return

    await update.message.reply_text(f"🚀 {len(targets)}개 채널 발행 시작...")

    for content_id, channel in targets:
        spec = get_channel(channel)
        if spec.publish_mode == PublishMode.MANUAL:
            # 수동: 알림만 + 완료 버튼
            keyboard = [[
                InlineKeyboardButton(
                    f"✅ {channel} 발행 완료",
                    callback_data=f"pubdone:{content_id}",
                )
            ]]
            await update.message.reply_text(
                f"📝 *{channel}* — 수동 발행 채널\n"
                f"본문을 복사해 직접 발행한 뒤, 아래 버튼을 눌러 주세요.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        else:
            result = dispatch(content_id, user_id)
            if result.ok:
                if result.raw and result.raw.get("manual"):
                    await update.message.reply_text(f"📝 {channel}: 수동 채널입니다")
                else:
                    await update.message.reply_text(
                        f"✅ {channel} 발행 완료\n🔗 {result.url or '(URL 없음)'}"
                    )
            else:
                await update.message.reply_text(f"❌ {channel} 실패: {result.error}")


@require_auth
async def on_pubdone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """수동 채널 ✅ 발행 완료 버튼 콜백."""
    query = update.callback_query
    await query.answer()
    content_id = int(query.data.split(":", 1)[1])

    context.user_data["pubdone_pending"] = content_id
    await query.edit_message_text(
        "🔗 발행된 URL을 메시지로 보내주세요.\n"
        "URL을 모르면 'skip' 입력."
    )


@require_auth
async def handle_pubdone_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """URL 입력 받아 published 상태로 변경."""
    content_id = context.user_data.get("pubdone_pending")
    if not content_id:
        return  # 이 흐름 아님

    url_text = (update.message.text or "").strip()
    context.user_data["pubdone_pending"] = None

    with get_session() as session:
        content = session.get(ChannelContent, content_id)
        if not content:
            await update.message.reply_text("⚠️ 콘텐츠 없음")
            return
        content.status = "published"
        content.published_at = _now_naive_utc()
        if url_text.lower() != "skip" and url_text.startswith("http"):
            content.published_url = url_text
        channel = content.channel

    await update.message.reply_text(
        f"✅ {channel} 발행 완료 처리됨"
        + (f"\n🔗 {url_text}" if url_text.startswith("http") else "")
    )


@require_auth
async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/schedule — 프로젝트의 publish_at 시간으로 모든 채널 스케줄 등록."""
    project_id = context.user_data.get("project_id")
    if not project_id:
        await update.message.reply_text("⚠️ 진행 중인 프로젝트가 없습니다.")
        return

    with get_session() as session:
        project = session.get(Project, project_id)
        if not project or not project.publish_at:
            await update.message.reply_text("⚠️ 프로젝트에 발행 시점이 없습니다.")
            return
        try:
            publish_at = datetime.strptime(project.publish_at, "%Y-%m-%d %H:%M")
        except ValueError:
            await update.message.reply_text(
                f"⚠️ 발행 시점 형식 오류: '{project.publish_at}' (YYYY-MM-DD HH:MM 형식 필요)"
            )
            return

        contents = (
            session.query(ChannelContent)
            .filter_by(project_id=project_id, status="ready")
            .all()
        )
        if not contents:
            await update.message.reply_text("⚠️ ready 상태 채널 없음")
            return

        schedule_ids = []
        for c in contents:
            sch = Schedule(
                project_id=project_id,
                channel=c.channel,
                publish_at=publish_at,
                publish_mode=get_channel(c.channel).publish_mode.value,
            )
            session.add(sch)
            session.flush()
            schedule_ids.append(sch.id)

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    app = context.application
    for sid in schedule_ids:
        add_schedule(app, sid, user_id, chat_id)

    await update.message.reply_text(
        f"⏰ {len(schedule_ids)}개 채널 스케줄 등록\n"
        f"발행 시각: {publish_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"5분 전 알림 + 자동/반자동 채널은 정시 발행"
    )
