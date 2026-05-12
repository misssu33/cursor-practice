"""/history — 완료 프로젝트 목록."""
from telegram import Update
from telegram.ext import ContextTypes

from storage import get_session
from storage.models import Project, ChannelContent
from utils import require_auth, send_md


@require_auth
async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_session() as session:
        rows = (
            session.query(Project)
            .filter(Project.user_id == user_id)
            .order_by(Project.updated_at.desc())
            .limit(20)
            .all()
        )
        items = []
        for p in rows:
            published = (
                session.query(ChannelContent)
                .filter_by(project_id=p.id, status="published")
                .count()
            )
            total = (
                session.query(ChannelContent)
                .filter_by(project_id=p.id)
                .count()
            )
            items.append((p.id, p.topic, p.status, p.updated_at, published, total))

    if not items:
        await update.message.reply_text("📭 이력이 없습니다.")
        return

    lines = ["📜 *프로젝트 이력* (최근 20개)\n"]
    for pid, topic, status, updated, pub, total in items:
        lines.append(
            f"#{pid} · {topic[:40]}\n"
            f"   상태: _{status}_ · 발행 {pub}/{total} · {updated.strftime('%m-%d %H:%M')}"
        )
    lines.append("\n자세히 보기: /export <id>")
    await send_md(update, "\n".join(lines))
