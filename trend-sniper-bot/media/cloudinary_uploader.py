"""Cloudinary 이미지 호스팅 (인스타 발행용)."""
from typing import Optional
from config import (
    CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET,
)
from utils.logger import get_logger

logger = get_logger(__name__)
_configured = False


def is_configured() -> bool:
    return bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)


def _ensure_config():
    global _configured
    if _configured:
        return
    import cloudinary
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )
    _configured = True


def upload_file(file_path: str, folder: str = "trend-sniper") -> Optional[str]:
    """로컬 파일 → Cloudinary URL."""
    if not is_configured():
        logger.warning("Cloudinary 미설정 — 업로드 skip")
        return None
    try:
        _ensure_config()
        from cloudinary import uploader
        res = uploader.upload(file_path, folder=folder, resource_type="image")
        return res.get("secure_url")
    except Exception as e:
        logger.error(f"cloudinary upload 실패: {e}")
        return None


def upload_bytes(data: bytes, filename: str = "image.jpg", folder: str = "trend-sniper") -> Optional[str]:
    """바이트 데이터 → Cloudinary URL."""
    if not is_configured():
        return None
    try:
        _ensure_config()
        from cloudinary import uploader
        import io
        res = uploader.upload(io.BytesIO(data), folder=folder, public_id=filename.rsplit(".", 1)[0])
        return res.get("secure_url")
    except Exception as e:
        logger.error(f"cloudinary upload_bytes 실패: {e}")
        return None
