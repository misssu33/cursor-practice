"""/resume — 중단된 프로젝트 이어하기."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from storage import get_session
from storage.models import Project
from utils import require_auth


@require_auth
async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_session() as session:
        rows = (
            session.query(Project)
            .filter(Project.user_id == user_id)
            .filter(Project.status.in_([
                "intake", "scanned", "core",
                "factcheck_done", "factcheck_skipped", "writing",
            ]))
            .order_by(Project.updated_at.desc())
            .limit(10)
            .all()
        )
        items = [(p.id, p.topic, p.status, p.updated_at) for p in rows]

    if not items:
        await update.message.reply_text("📭 이어할 프로젝트가 없습니다.")
        return

    text = "⏯ *이어할 프로젝트 선택*\n\n"
    buttons = []
    for pid, topic, status, updated in items:
        text += f"#{pid} · {topic[:40]} · _{status}_ · {updated.strftime('%m-%d %H:%M')}\n"
        buttons.append([InlineKeyboardButton(
            f"#{pid} {topic[:30]}", callback_data=f"resume:{pid}"
        )])

    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@require_auth
async def on_resume_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":", 1)[1])

    with get_session() as session:
        project = session.get(Project, project_id)
        if not project or project.user_id != update.effective_user.id:
            await query.edit_message_text("⚠️ 프로젝트 없음")
            return
        status = project.status
        topic = project.topic

    context.user_data["project_id"] = project_id

    next_step = {
        "intake": "/core 로 코어시트 작성",
        "scanned": "/core 로 코어시트 작성",
        "core": "/fc_yes 팩트체크 또는 /ch_* 채널 작성",
        "factcheck_done": "/ch_linkedin /ch_naver /ch_adsense /ch_instagram /ch_threads",
        "factcheck_skipped": "/ch_linkedin /ch_naver /ch_adsense /ch_instagram /ch_threads",
        "writing": "/ch_done 으로 작성 마무리 → /publish",
    }.get(status, "/ch_done → /publish")

    await query.edit_message_text(
        f"✅ 프로젝트 #{project_id} 로 복귀\n"
        f"📌 {topic}\n"
        f"📍 현재 상태: _{status}_\n\n"
        f"⏭️ 다음 단계: {next_step}",
        parse_mode="Markdown",
    )
