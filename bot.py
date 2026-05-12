import os
import asyncio
import logging
from dotenv import load_dotenv

# 환경변수 먼저 로드 (다른 모듈 import 전에 필수)
load_dotenv()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from rss import fetch_latest_entries
from summarizer import summarize
from threads import post_to_threads

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))


def is_allowed(update: Update) -> bool:
    return update.effective_user.id == ALLOWED_USER_ID


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📡 RSS → Threads 봇\n\n"
        "/preview <RSS URL> — 요약 미리보기\n"
        "/summarize <RSS URL> [개수] — 요약 후 Threads에 게시"
    )


async def preview(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("권한이 없습니다.")
        return
    if not ctx.args:
        await update.message.reply_text("사용법: /preview <RSS URL>")
        return

    url = ctx.args[0]
    await update.message.reply_text("⏳ 요약 생성 중...")

    try:
        entries = fetch_latest_entries(url, limit=3)
        for i, e in enumerate(entries):
            if i > 0:
                await asyncio.sleep(4)  # Gemini 무료 등급 분당 한도 회피
            summary = summarize(e["title"], e["summary"])
            await update.message.reply_text(
                f"📰 {e['title']}\n\n{summary}\n\n🔗 {e['link']}"
            )
    except Exception as ex:
        await update.message.reply_text(f"❌ 오류: {ex}")


async def summarize_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("권한이 없습니다.")
        return
    if not ctx.args:
        await update.message.reply_text("사용법: /summarize <RSS URL> [개수]")
        return

    url = ctx.args[0]
    limit = int(ctx.args[1]) if len(ctx.args) > 1 else 1

    await update.message.reply_text(f"⏳ 처리 중... ({limit}건)")

    try:
        entries = fetch_latest_entries(url, limit=limit)
        for i, e in enumerate(entries):
            if i > 0:
                await asyncio.sleep(4)  # Gemini 무료 등급 분당 한도 회피
            summary = summarize(e["title"], e["summary"])
            post_id = post_to_threads(summary)
            await update.message.reply_text(
                f"✅ 게시 완료\n제목: {e['title']}\nThreads ID: {post_id}"
            )
    except Exception as ex:
        await update.message.reply_text(f"❌ 오류: {ex}")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("summarize", summarize_cmd))

    print("🤖 봇이 실행 중입니다. (Ctrl+C로 종료)")
    app.run_polling()


if __name__ == "__main__":
    main()
