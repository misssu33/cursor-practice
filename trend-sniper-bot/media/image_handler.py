"""인스타 이미지 처리 — A안(단일) + B안(미디어그룹) 자동 호환."""
from datetime import datetime, timezone
from pathlib import Path
from telegram import Update, Message
from telegram.ext import ContextTypes
from utils.logger import get_logger
from media.cloudinary_uploader import upload_file, is_configured as cdn_configured

logger = get_logger(__name__)

LOCAL_DIR = Path("./data/instagram_images")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)


async def save_telegram_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    content_id: int,
    seq: int,
) -> dict:
    """텔레그램 첨부 사진 → 로컬 저장 + Cloudinary 업로드.

    Returns:
        {seq, local_path, cloud_url, upload_mode, media_group_id}
    """
    msg: Message = update.message
    if not msg or not msg.photo:
        return {}

    photo = msg.photo[-1]  # 가장 큰 해상도
    tg_file = await context.bot.get_file(photo.file_id)
    # tz-aware UTC → cp949 안전한 ASCII 타임스탬프.
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    local_path = LOCAL_DIR / f"c{content_id}_s{seq:02d}_{ts}.jpg"
    await tg_file.download_to_drive(str(local_path))

    cloud_url = None
    if cdn_configured():
        cloud_url = upload_file(str(local_path), folder=f"trend-sniper/c{content_id}")

    # media_group_id 유무로 모드 판별
    mode = "group" if msg.media_group_id else "single"

    logger.info(
        f"이미지 저장: content={content_id}, seq={seq}, mode={mode}, "
        f"cloud={'O' if cloud_url else 'X'}"
    )

    return {
        "seq": seq,
        "local_path": str(local_path),
        "cloud_url": cloud_url,
        "upload_mode": mode,
        "media_group_id": msg.media_group_id or "",
    }
