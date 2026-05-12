"""/connect — OAuth A안 (inline code)."""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from conversation import State
from oauth import blogger_oauth, threads_oauth, instagram_oauth
from utils import require_auth, get_logger

logger = get_logger(__name__)


@require_auth
async def cmd_connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/connect <provider> — blogger / threads / instagram."""
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "사용법: /connect <provider>\n"
            "지원: blogger, threads, instagram\n\n"
            "예) /connect blogger"
        )
        return ConversationHandler.END

    provider = args[0].lower()
    user_id = update.effective_user.id

    if provider == "blogger":
        try:
            auth_url, state = blogger_oauth.get_auth_url()
        except FileNotFoundError as e:
            await update.message.reply_text(f"⚠️ {e}")
            return ConversationHandler.END
        except Exception as e:
            await update.message.reply_text(f"❌ OAuth URL 생성 실패: {e}")
            return ConversationHandler.END

        context.user_data["connect_provider"] = "blogger"
        await update.message.reply_text(
            f"🔐 *Blogger OAuth*\n\n"
            f"1) 아래 URL을 브라우저에서 여세요:\n{auth_url}\n\n"
            f"2) Google 로그인 후 발급된 *인증 코드*를 이 채팅에 그대로 붙여넣으세요.",
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        return State.CONNECT_WAITING_CODE

    elif provider == "threads":
        res = threads_oauth.verify_and_save(user_id)
        if res["ok"]:
            await update.message.reply_text(
                f"✅ Threads 연결 OK\n사용자: @{res.get('username', '?')}"
            )
        else:
            await update.message.reply_text(f"❌ {res['error']}")
        return ConversationHandler.END

    elif provider == "instagram":
        res = instagram_oauth.verify_and_save(user_id)
        if res["ok"]:
            await update.message.reply_text(
                f"✅ Instagram 연결 OK\n사용자: @{res.get('username', '?')}"
            )
        else:
            await update.message.reply_text(f"❌ {res['error']}")
        return ConversationHandler.END

    else:
        await update.message.reply_text(f"⚠️ 지원하지 않는 provider: {provider}")
        return ConversationHandler.END


@require_auth
async def handle_connect_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Blogger OAuth 코드 입력 처리."""
    code = (update.message.text or "").strip()
    if not code or len(code) < 10:
        await update.message.reply_text("⚠️ 유효하지 않은 코드입니다. 다시 붙여넣어 주세요.")
        return State.CONNECT_WAITING_CODE

    provider = context.user_data.get("connect_provider")
    user_id = update.effective_user.id

    if provider == "blogger":
        try:
            res = blogger_oauth.exchange_code(code, user_id)
            await update.message.reply_text(
                f"✅ Blogger 연결 완료\n토큰 만료: {res.get('expires_at') or '(N/A)'}"
            )
        except Exception as e:
            logger.error(f"Blogger code 교환 실패: {e}", exc_info=True)
            await update.message.reply_text(f"❌ 코드 교환 실패: {e}")

    context.user_data["connect_provider"] = None
    return ConversationHandler.END
