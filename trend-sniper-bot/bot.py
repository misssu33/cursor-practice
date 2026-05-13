"""트렌드 스나이퍼 봇 — Part 4 최종 통합 엔트리포인트.

명령 흐름:
  /new → 인테이크 → 자동 스캔 → /core → /fc_yes|/fc_no →
  /ch_linkedin /ch_naver /ch_adsense /ch_instagram /ch_threads → /ch_done →
  /publish (즉시) 또는 /schedule (예약) → /connect / /history / /resume / /export
"""
import sys
from pathlib import Path
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
from scheduler import start as start_scheduler
from handlers import (
    scan_handler, core_handler, factcheck_handler,
    channel_handler, instagram_image_handler,
    publish_handler, connect_handler,
    resume_handler, history_handler, export_handler,
    timing_handler,
)

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


# ===== /new =====

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

    await update.message.reply_text(
        f"✅ 양식 접수 완료 (프로젝트 #{project_id})\n"
        f"📌 {form.topic} · 🔑 {form.main_keyword}"
    )
    await scan_handler.run_scan(update, context, project_id)
    return ConversationHandler.END


# ===== 텍스트 메시지 분기 (수동 발행 URL 입력 vs 일반) =====

@require_auth
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ConversationHandler 외부 텍스트 메시지 라우팅."""
    if context.user_data.get("pubdone_pending"):
        await publish_handler.handle_pubdone_url(update, context)
        return
    # 그 외는 무시 — 도움말은 명시 명령으로.


# ===== 마이그레이션 자동 실행 =====

def _run_migrations() -> None:
    """봇 부팅 시 마이그레이션 자동 실행 (idempotent)."""
    try:
        import importlib.util
        mig_path = Path(__file__).parent / "migrations" / "001_add_unique_constraints.py"
        if mig_path.exists():
            spec = importlib.util.spec_from_file_location("mig001", mig_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.run()
    except Exception as e:
        logger.warning(f"마이그레이션 스킵: {e}")


# ===== 앱 빌드 =====

def build_app() -> Application:
    missing = validate_config()
    if missing:
        logger.error(f"필수 환경 변수 누락: {missing}")
        print(f"❌ .env에 다음 항목을 설정하세요: {', '.join(missing)}")
        sys.exit(1)

    ensure_dirs()
    init_db()
    _run_migrations()

    # AsyncIOScheduler 는 이벤트 루프 안에서 start() 해야 하므로 post_init 으로 미룬다.
    async def _post_init(app: Application) -> None:
        start_scheduler()

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    # 기본
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))

    # /new
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("new", cmd_new)],
        states={State.INTAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_intake)]},
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    ))

    # /core
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("core", core_handler.cmd_core)],
        states={State.CORE_SHEET: [MessageHandler(filters.TEXT & ~filters.COMMAND, core_handler.handle_core_input)]},
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    ))

    # /fc_yes
    app.add_handler(ConversationHandler(
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
    ))
    app.add_handler(CommandHandler("fc_no", factcheck_handler.cmd_fc_no))

    # /connect
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("connect", connect_handler.cmd_connect)],
        states={
            State.CONNECT_WAITING_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, connect_handler.handle_connect_code),
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    ))

    # 5채널 작성
    app.add_handler(CommandHandler("ch_linkedin", channel_handler.cmd_ch_linkedin))
    app.add_handler(CommandHandler("ch_naver", channel_handler.cmd_ch_naver))
    app.add_handler(CommandHandler("ch_adsense", channel_handler.cmd_ch_adsense))
    app.add_handler(CommandHandler("ch_instagram", channel_handler.cmd_ch_instagram))
    app.add_handler(CommandHandler("ch_threads", channel_handler.cmd_ch_threads))
    app.add_handler(CommandHandler("ch_done", channel_handler.cmd_ch_done))

    # 인스타 이미지 업로드
    app.add_handler(CallbackQueryHandler(instagram_image_handler.on_upload_start, pattern=r"^ig_upload_start$"))
    app.add_handler(CallbackQueryHandler(instagram_image_handler.on_skip, pattern=r"^ig_skip$"))
    app.add_handler(CommandHandler("ig_done", instagram_image_handler.cmd_ig_done))
    app.add_handler(CommandHandler("ig_cancel", instagram_image_handler.cmd_ig_cancel))
    app.add_handler(MessageHandler(filters.PHOTO, instagram_image_handler.on_photo))

    # 발행
    app.add_handler(CommandHandler("publish", publish_handler.cmd_publish))
    app.add_handler(CommandHandler("schedule", publish_handler.cmd_schedule))
    app.add_handler(CallbackQueryHandler(publish_handler.on_pubdone, pattern=r"^pubdone:"))

    # /resume /history /export /timing
    app.add_handler(CommandHandler("resume", resume_handler.cmd_resume))
    app.add_handler(CallbackQueryHandler(resume_handler.on_resume_select, pattern=r"^resume:"))
    app.add_handler(CommandHandler("history", history_handler.cmd_history))
    app.add_handler(CommandHandler("export", export_handler.cmd_export))
    app.add_handler(CommandHandler("timing", timing_handler.cmd_timing))

    # 텍스트 라우터 (수동 발행 URL 입력 등)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    app.add_handler(CommandHandler("cancel", cmd_cancel))

    # 스케줄러는 위의 post_init 훅에서 이벤트 루프 안에서 시작한다.

    return app


def main() -> None:
    logger.info("🚀 트렌드 스나이퍼 봇 시작 (Part 4 — 최종)")
    app = build_app()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
