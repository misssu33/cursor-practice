"""Blogger OAuth — A안(inline code, 헤드리스 호환).

흐름: /connect blogger → 봇이 auth_url 발급 → 사용자가 브라우저에서 동의 → 발급된 코드를 텔레그램에 붙여넣기
     → exchange_code 가 토큰 저장(refresh_token 포함) → 이후 get_credentials 가 자동 갱신.
"""
import json
from pathlib import Path
from config import BLOGGER_CLIENT_SECRETS
from storage import get_session
from storage.models import OAuthToken
from utils.logger import get_logger

logger = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/blogger"]


def get_auth_url() -> tuple[str, str]:
    """OAuth 인증 URL + state 반환."""
    if not Path(BLOGGER_CLIENT_SECRETS).exists():
        raise FileNotFoundError(
            f"Blogger client secrets 파일 없음: {BLOGGER_CLIENT_SECRETS}\n"
            "Google Cloud Console → OAuth 클라이언트(데스크톱 앱) JSON 다운로드 필요."
        )
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_secrets_file(
        BLOGGER_CLIENT_SECRETS,
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob",  # OOB = inline code
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    return auth_url, state


def exchange_code(code: str, user_id: int) -> dict:
    """사용자가 받은 코드 → 토큰 교환 + DB 저장."""
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_secrets_file(
        BLOGGER_CLIENT_SECRETS,
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob",
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    expires_at = None
    if creds.expiry:
        expires_at = creds.expiry

    with get_session() as session:
        existing = session.query(OAuthToken).filter_by(
            user_id=user_id, provider="blogger"
        ).first()
        token_data = {
            "user_id": user_id,
            "provider": "blogger",
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "expires_at": expires_at,
            "extra": {"scopes": SCOPES, "client_id": creds.client_id},
        }
        if existing:
            for k, v in token_data.items():
                setattr(existing, k, v)
        else:
            session.add(OAuthToken(**token_data))

    logger.info(f"Blogger 토큰 저장: user={user_id}")
    return {"ok": True, "expires_at": expires_at}


def get_credentials(user_id: int):
    """저장된 토큰 → Credentials 객체 (자동 refresh)."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    with get_session() as session:
        tok = session.query(OAuthToken).filter_by(
            user_id=user_id, provider="blogger"
        ).first()
        if not tok:
            return None

        with open(BLOGGER_CLIENT_SECRETS) as f:
            client_data = json.load(f)
        secrets = client_data.get("installed") or client_data.get("web") or {}

        creds = Credentials(
            token=tok.access_token,
            refresh_token=tok.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=secrets.get("client_id"),
            client_secret=secrets.get("client_secret"),
            scopes=SCOPES,
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            tok.access_token = creds.token
            if creds.expiry:
                tok.expires_at = creds.expiry
            logger.info(f"Blogger 토큰 자동 갱신: user={user_id}")

    return creds


def is_connected(user_id: int) -> bool:
    with get_session() as session:
        return session.query(OAuthToken).filter_by(
            user_id=user_id, provider="blogger"
        ).first() is not None
