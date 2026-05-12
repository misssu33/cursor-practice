"""트렌드 스나이퍼 봇 — Part 2 통합."""
import sys
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, CallbackQueryHandler, filters,
)

from config import TELEGRAM_BOT_TOKEN, validate_config, ensure_dirs
from conversation import State, messages, parse_form
from storage import init_db, get_session
from storage.models import Project
from utils import require_auth, get_logger, send_md
from handlers import scan_handler, core_handler, factcheck_handler

logger = get_logger(__name__)


# ===== 기본 명령 =====

@require_auth
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_md(update, messages.WELCOME)


@require_auth
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_md(update, messages.HELP)


@require_auth
async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(messages.CANCEL)
    return ConversationHandler.END


# ===== /new 흐름 =====

@require_auth
async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await send_md(update, messages.INTAKE_FORM)
    return State.INTAKE


@require_auth
async def handle_intake(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text or ""
    form = parse_form(text)
    if not form:
        await update.message.reply_text(messages.INTAKE_PARSE_FAIL)
        return State.INTAKE

    user_id = update.effective_user.id
    with get_session() as session:
        project = Project(
            user_id=user_id,
            topic=form.topic,
            audience=form.audience,
            main_keyword=form.main_keyword,
            sub_keywords=form.sub_keywords,
            goal=form.goal,
            tone=form.tone,
            publish_at=form.publish_at,
            differentiation=form.differentiation,
            cta=form.cta,
            status="intake",
        )
        session.add(project)
        session.flush()
        project_id = project.id

    context.user_data["project_id"] = project_id
    logger.info(f"신규 프로젝트 #{project_id}: {form.topic}")

    await update.message.reply_text(
        f"✅ 양식 접수 완료 (프로젝트 #{project_id})\n"
        f"📌 {form.topic} · 🔑 {form.main_keyword}\n"
        f"🔑 서브: {', '.join(form.sub_keywords)}"
    )

    # 자동 트렌드 스캔 실행
    await scan_handler.run_scan(update, context, project_id)
    return ConversationHandler.END


# ===== Part 3~4 스텁 =====

@require_auth
async def cmd_stub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.split()[0] if update.message.text else "?"
    part_map = {
        "/resume": 4, "/history": 4, "/export": 4, "/connect": 4,
        "/ch_linkedin": 3, "/ch_naver": 3, "/ch_adsense": 3,
        "/ch_instagram": 3, "/ch_threads": 3, "/ch_done": 3,
    }
    part = part_map.get(cmd, 3)
    await update.message.reply_text(messages.NOT_IMPLEMENTED.format(part=part))


# ===== 앱 빌드 =====

def build_app() -> Application:
    missing = validate_config()
    if missing:
        logger.error(f"필수 환경 변수 누락: {missing}")
        print(f"❌ .env에 다음 항목을 설정하세요: {', '.join(missing)}")
        sys.exit(1)

    ensure_dirs()
    init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 기본 명령
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))

    # /new — 양식 입력
    conv_new = ConversationHandler(
        entry_points=[CommandHandler("new", cmd_new)],
        states={
            State.INTAKE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_intake),
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv_new)

    # /core — 코어시트
    conv_core = ConversationHandler(
        entry_points=[CommandHandler("core", core_handler.cmd_core)],
        states={
            State.CORE_SHEET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, core_handler.handle_core_input),
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv_core)

    # /fc_yes — 팩트체크 흐름
    conv_fc = ConversationHandler(
        entry_points=[CommandHandler("fc_yes", factcheck_handler.cmd_fc_yes)],
        states={
            State.FACTCHECK_CLAIM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, factcheck_handler.handle_claim),
            ],
            State.FACTCHECK_VERDICT: [
                CallbackQueryHandler(factcheck_handler.handle_verdict, pattern=r"^fc_v:"),
                CallbackQueryHandler(factcheck_handler.handle_next, pattern=r"^fc_(more|done)$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            CommandHandler("fc_no", factcheck_handler.cmd_fc_no),
        ],
        allow_reentry=True,
    )
    app.add_handler(conv_fc)

    # 팩트체크 단독 명령
    app.add_handler(CommandHandler("fc_no", factcheck_handler.cmd_fc_no))

    # Part 3~4 스텁
    for cmd in [
        "resume", "history", "export", "connect",
        "ch_linkedin", "ch_naver", "ch_adsense", "ch_instagram", "ch_threads", "ch_done",
    ]:
        app.add_handler(CommandHandler(cmd, cmd_stub))

    app.add_handler(CommandHandler("cancel", cmd_cancel))
    return app


def main() -> None:
    logger.info("🚀 트렌드 스나이퍼 봇 시작 (Part 2)")
    app = build_app()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
