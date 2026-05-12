"""Instagram Graph API — .env 장기 토큰 + 검증."""
import requests
from config import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ID
from storage import get_session
from storage.models import OAuthToken
from utils.logger import get_logger

logger = get_logger(__name__)


def is_configured() -> bool:
    return bool(INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ID)


def verify_and_save(user_id: int) -> dict:
    if not is_configured():
        return {"ok": False, "error": ".env에 INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_BUSINESS_ID 미설정"}

    try:
        r = requests.get(
            f"https://graph.facebook.com/v20.0/{INSTAGRAM_BUSINESS_ID}",
            params={"fields": "id,username,name", "access_token": INSTAGRAM_ACCESS_TOKEN},
            timeout=8,
        )
        r.raise_for_status()
        info = r.json()
    except Exception as e:
        return {"ok": False, "error": f"토큰 검증 실패: {e}"}

    with get_session() as session:
        existing = session.query(OAuthToken).filter_by(
            user_id=user_id, provider="instagram"
        ).first()
        payload = {
            "user_id": user_id,
            "provider": "instagram",
            "access_token": INSTAGRAM_ACCESS_TOKEN,
            "refresh_token": None,
            "expires_at": None,
            "extra": {"business_id": INSTAGRAM_BUSINESS_ID, "username": info.get("username")},
        }
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
        else:
            session.add(OAuthToken(**payload))

    logger.info(f"Instagram 토큰 검증 OK: user={user_id}, username={info.get('username')}")
    return {"ok": True, "username": info.get("username")}


def is_connected(user_id: int) -> bool:
    with get_session() as session:
        return session.query(OAuthToken).filter_by(
            user_id=user_id, provider="instagram"
        ).first() is not None
