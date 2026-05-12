"""인스타그램 이미지 업로드 핸들러 — A안(단일) + B안(미디어그룹) 호환."""
from telegram import Update
from telegram.ext import ContextTypes

from media.image_handler import save_telegram_photo
from storage import get_session
from storage.models import InstagramImage, ChannelContent
from utils import require_auth, get_logger

logger = get_logger(__name__)


@require_auth
async def on_upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📷 이미지 업로드 시작 버튼."""
    query = update.callback_query
    await query.answer()
    expected = context.user_data.get("instagram_expected_slides", 8)
    context.user_data["instagram_uploading"] = True
    context.user_data["instagram_uploaded"] = []

    await query.edit_message_text(
        f"📷 이미지 업로드 모드 ON\n\n"
        f"슬라이드 {expected}장에 대응하는 이미지를 보내주세요.\n"
        f"• 1장씩 또는 여러 장 묶어서 모두 가능\n"
        f"• 끝나면 /ig_done\n"
        f"• 취소: /ig_cancel"
    )


@require_auth
async def on_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⏭️ 이미지 나중에 버튼."""
    query = update.callback_query
    await query.answer()
    context.user_data["instagram_uploading"] = False
    await query.edit_message_text(
        "⏭️ 이미지는 나중에 업로드할 수 있습니다.\n"
        "재개하려면 /ch_instagram 다시 실행 후 📷 버튼을 누르세요."
    )


@require_auth
async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """사진 메시지 수신 — 업로드 모드일 때만 처리."""
    if not context.user_data.get("instagram_uploading"):
        return  # 다른 흐름의 사진은 무시

    content_id = context.user_data.get("instagram_content_id")
    if not content_id:
        await update.message.reply_text("⚠️ 인스타 콘텐츠가 지정되지 않았습니다.")
        return

    uploaded = context.user_data.get("instagram_uploaded", [])
    next_seq = len(uploaded) + 1

    info = await save_telegram_photo(update, context, content_id, next_seq)
    if not info:
        await update.message.reply_text("⚠️ 사진 처리 실패")
        return

    # DB 저장 — media_group_id 는 인스타 발행 API 가 사용하지 않으므로 저장하지 않는다
    with get_session() as session:
        session.add(InstagramImage(
            content_id=content_id,
            seq=next_seq,
            local_path=info["local_path"],
            cloud_url=info["cloud_url"] or "",
            upload_mode=info["upload_mode"],
        ))

    uploaded.append(info)
    context.user_data["instagram_uploaded"] = uploaded

    expected = context.user_data.get("instagram_expected_slides", 8)
    mode_label = "📦 미디어그룹(B)" if info["upload_mode"] == "group" else "📷 단일(A)"
    cdn_label = "☁️ 업로드됨" if info["cloud_url"] else "💾 로컬만"

    await update.message.reply_text(
        f"✅ {next_seq}/{expected}장 저장 ({mode_label}, {cdn_label})"
    )

    if next_seq >= expected:
        await update.message.reply_text(
            f"🎉 슬라이드 수만큼 업로드 완료. /ig_done 으로 마무리하세요."
        )


@require_auth
async def cmd_ig_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """업로드 종료."""
    uploaded = context.user_data.get("instagram_uploaded", [])
    expected = context.user_data.get("instagram_expected_slides", 0)
    content_id = context.user_data.get("instagram_content_id")

    context.user_data["instagram_uploading"] = False

    if not uploaded:
        await update.message.reply_text("⚠️ 업로드된 이미지가 없습니다.")
        return

    # ContentStatus 갱신
    with get_session() as session:
        content = session.get(ChannelContent, content_id)
        if content:
            content.status = "ready"

    cloud_ok = sum(1 for u in uploaded if u.get("cloud_url"))
    single = sum(1 for u in uploaded if u.get("upload_mode") == "single")
    group = sum(1 for u in uploaded if u.get("upload_mode") == "group")

    await update.message.reply_text(
        f"📷 *인스타 이미지 업로드 완료*\n\n"
        f"총 {len(uploaded)}장 / 예상 {expected}장\n"
        f"• 단일(A) {single} · 그룹(B) {group}\n"
        f"• Cloudinary 업로드: {cloud_ok}/{len(uploaded)}\n\n"
        f"발행 단계는 Part 4에서 연결됩니다.",
        parse_mode="Markdown",
    )


@require_auth
async def cmd_ig_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["instagram_uploading"] = False
    await update.message.reply_text("❌ 이미지 업로드를 취소했습니다.")
