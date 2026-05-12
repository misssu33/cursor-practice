"""코어시트 입력 핸들러."""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from conversation import State, messages, parse_core_sheet
from storage import get_session
from storage.models import Project, CoreSheetRow
from utils import require_auth, get_logger, send_md

logger = get_logger(__name__)


@require_auth
async def cmd_core(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/core — 코어시트 양식 발송."""
    project_id = context.user_data.get("project_id")
    if not project_id:
        await update.message.reply_text(
            "⚠️ 진행 중인 프로젝트가 없습니다. /new 로 시작하세요."
        )
        return ConversationHandler.END

    await send_md(update, messages.CORE_SHEET_FORM)
    return State.CORE_SHEET


@require_auth
async def handle_core_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text or ""
    sheet = parse_core_sheet(text)
    if not sheet:
        await update.message.reply_text(
            "⚠️ 코어시트 양식을 인식하지 못했습니다.\n"
            "모든 항목(메인메시지·후킹·데이터·사례·인사이트)을 채워주세요."
        )
        return State.CORE_SHEET

    project_id = context.user_data.get("project_id")
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            await update.message.reply_text("⚠️ 프로젝트 없음")
            return ConversationHandler.END

        existing = session.query(CoreSheetRow).filter_by(project_id=project_id).first()
        if existing:
            existing.main_message = sheet.main_message
            existing.hooks = sheet.hooks
            existing.data_points = sheet.data_points
            existing.cases = sheet.cases
            existing.insights = sheet.insights
        else:
            session.add(CoreSheetRow(
                project_id=project_id,
                main_message=sheet.main_message,
                hooks=sheet.hooks,
                data_points=sheet.data_points,
                cases=sheet.cases,
                insights=sheet.insights,
            ))
        project.status = "core"

    response = (
        f"✅ 코어시트 저장 완료 (프로젝트 #{project_id})\n\n"
        f"💬 메인: {sheet.main_message}\n"
        f"🎣 후킹: {len(sheet.hooks)}개\n"
        f"📊 데이터: {len(sheet.data_points)}개\n"
        f"📂 사례: {len(sheet.cases)}개\n"
        f"💡 인사이트: {len(sheet.insights)}개\n\n"
        f"{messages.FACTCHECK_PROMPT}"
    )
    await send_md(update, response)
    return ConversationHandler.END
