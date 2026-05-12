"""Threads OAuth — .env의 장기 토큰 사용 (Meta는 inline code 미지원).

Threads API는 Long-lived Access Token을 .env에 저장하는 방식이 표준입니다.
/connect threads 는 토큰 유효성 점검 + DB 동기화 역할.
"""
import requests
from config import THREADS_ACCESS_TOKEN, THREADS_USER_ID
from storage import get_session
from storage.models import OAuthToken
from utils.logger import get_logger

logger = get_logger(__name__)


def is_configured() -> bool:
    return bool(THREADS_ACCESS_TOKEN and THREADS_USER_ID)


def verify_and_save(user_id: int) -> dict:
    """현재 .env 토큰으로 본인 정보 조회 → 성공 시 DB 저장."""
    if not is_configured():
        return {"ok": False, "error": ".env에 THREADS_ACCESS_TOKEN / THREADS_USER_ID 미설정"}

    try:
        r = requests.get(
            f"https://graph.threads.net/v1.0/{THREADS_USER_ID}",
            params={"fields": "id,username", "access_token": THREADS_ACCESS_TOKEN},
            timeout=8,
        )
        r.raise_for_status()
        info = r.json()
    except Exception as e:
        return {"ok": False, "error": f"토큰 검증 실패: {e}"}

    with get_session() as session:
        existing = session.query(OAuthToken).filter_by(
            user_id=user_id, provider="threads"
        ).first()
        payload = {
            "user_id": user_id,
            "provider": "threads",
            "access_token": THREADS_ACCESS_TOKEN,
            "refresh_token": None,
            "expires_at": None,
            "extra": {"threads_user_id": THREADS_USER_ID, "username": info.get("username")},
        }
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
        else:
            session.add(OAuthToken(**payload))

    logger.info(f"Threads 토큰 검증 OK: user={user_id}, username={info.get('username')}")
    return {"ok": True, "username": info.get("username")}


def is_connected(user_id: int) -> bool:
    with get_session() as session:
        return session.query(OAuthToken).filter_by(
            user_id=user_id, provider="threads"
        ).first() is not None
