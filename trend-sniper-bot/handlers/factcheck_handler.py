"""팩트체크 핸들러 — A안(수동 판정) + B-2(출처 자동 분류)."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from conversation import State
from factcheck import collect_sources, format_sources, all_verdicts, VERDICT_LABELS
from storage import get_session
from storage.models import Project, FactCheck
from utils import require_auth, get_logger, send_md

logger = get_logger(__name__)


@require_auth
async def cmd_fc_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/fc_yes — 검증할 주장 입력 대기."""
    project_id = context.user_data.get("project_id")
    if not project_id:
        await update.message.reply_text("⚠️ 진행 중인 프로젝트가 없습니다.")
        return ConversationHandler.END

    await update.message.reply_text(
        "🔬 검증할 주장(통계·인용·사실)을 한 줄로 입력해 주세요.\n"
        "예) '2024년 한국 1인가구가 전체 가구의 35%를 넘었다'\n\n"
        "건너뛰려면 /fc_no"
    )
    return State.FACTCHECK_CLAIM


@require_auth
async def cmd_fc_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """팩트체크 건너뛰기."""
    project_id = context.user_data.get("project_id")
    with get_session() as session:
        project = session.get(Project, project_id)
        if project:
            project.status = "factcheck_skipped"

    await update.message.reply_text(
        "⏭️ 팩트체크를 건너뛰었습니다.\n"
        "이제 채널별 작성으로 진행하세요.\n\n"
        "/ch_linkedin · /ch_naver · /ch_adsense · /ch_instagram · /ch_threads"
    )
    return ConversationHandler.END


@require_auth
async def handle_claim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """사용자가 검증 대상 주장 입력 → 출처 자동 수집."""
    claim = (update.message.text or "").strip()
    if len(claim) < 5:
        await update.message.reply_text("⚠️ 너무 짧습니다. 다시 입력해 주세요.")
        return State.FACTCHECK_CLAIM

    context.user_data["fc_claim"] = claim
    await update.message.reply_text("🔍 관련 자료 수집 중...")

    import asyncio
    sources = await asyncio.to_thread(collect_sources, claim, 10)
    context.user_data["fc_sources"] = sources

    # 출처 목록 출력
    await send_md(update, format_sources(claim, sources))

    # 판정 버튼
    buttons = []
    row = []
    for code, label in all_verdicts():
        row.append(InlineKeyboardButton(label, callback_data=f"fc_v:{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("⏭️ 건너뛰기", callback_data="fc_v:SKIP")])

    await update.message.reply_text(
        "📝 자료를 검토한 뒤 판정을 선택해 주세요:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return State.FACTCHECK_VERDICT


@require_auth
async def handle_verdict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """판정 버튼 콜백 처리."""
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 1)[1]

    project_id = context.user_data.get("project_id")
    claim = context.user_data.get("fc_claim", "")
    sources = context.user_data.get("fc_sources", [])

    if code == "SKIP":
        await query.edit_message_text("⏭️ 판정을 건너뛰었습니다.")
        return await _to_channel_menu(update, context)

    # DB 저장
    with get_session() as session:
        session.add(FactCheck(
            project_id=project_id,
            claim=claim,
            sources=sources,
            verdict=code,
            note="",
        ))
        project = session.get(Project, project_id)
        if project:
            project.status = "factcheck_done"

    label = VERDICT_LABELS.get(code, code)
    from factcheck.verdicts import is_usable
    usable_note = "✅ 콘텐츠에 사용 가능" if is_usable(code) else "⚠️ 사용 시 주의 필요"

    await query.edit_message_text(
        f"📝 판정 저장: {label}\n{usable_note}\n\n"
        f"주장: _{claim[:120]}_"
    )

    # 추가 검증 or 채널 메뉴
    keyboard = [[
        InlineKeyboardButton("➕ 다른 주장 검증", callback_data="fc_more"),
        InlineKeyboardButton("✍️ 채널 작성으로", callback_data="fc_done"),
    ]]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="다음 단계를 선택하세요:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return State.FACTCHECK_VERDICT


@require_auth
async def handle_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """➕ 다른 주장 검증 / ✍️ 채널 메뉴 이동."""
    query = update.callback_query
    await query.answer()

    if query.data == "fc_more":
        await query.edit_message_text(
            "🔬 다음 검증할 주장을 입력해 주세요.\n건너뛰려면 /fc_no"
        )
        return State.FACTCHECK_CLAIM

    # fc_done
    await query.edit_message_text("✅ 팩트체크 완료. 채널 작성으로 이동합니다.")
    return await _to_channel_menu(update, context)


async def _to_channel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from conversation.messages import CHANNEL_MENU
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=CHANNEL_MENU, parse_mode="Markdown")
    return ConversationHandler.END
