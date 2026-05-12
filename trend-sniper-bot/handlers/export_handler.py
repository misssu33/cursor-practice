"""/export <project_id> — 채널별 파일 전송 (ZIP 미사용)."""
from telegram import Update
from telegram.ext import ContextTypes

from exporters import export_project
from storage import get_session
from storage.models import Project
from utils import require_auth, get_logger

logger = get_logger(__name__)


@require_auth
async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if not args:
        project_id = context.user_data.get("project_id")
        if not project_id:
            await update.message.reply_text("사용법: /export <project_id>")
            return
    else:
        try:
            project_id = int(args[0])
        except ValueError:
            await update.message.reply_text("⚠️ project_id는 숫자여야 합니다.")
            return

    user_id = update.effective_user.id
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project or project.user_id != user_id:
            await update.message.reply_text("⚠️ 프로젝트 없음 또는 권한 없음")
            return

    await update.message.reply_text(f"📦 프로젝트 #{project_id} 내보내는 중...")

    try:
        files = export_project(project_id)
    except Exception as e:
        logger.error(f"export 실패: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 내보내기 실패: {e}")
        return

    if not files:
        await update.message.reply_text("⚠️ 내보낼 콘텐츠가 없습니다.")
        return

    for channel, path in files:
        try:
            with open(path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=path.name,
                    caption=f"📄 {channel} ({path.suffix})",
                )
        except Exception as e:
            logger.error(f"파일 전송 실패 ({path}): {e}")

    await update.message.reply_text(
        f"✅ 내보내기 완료: {len(files)}개 파일\n"
        f"📁 서버 경로: {files[0][1].parent}"
    )
