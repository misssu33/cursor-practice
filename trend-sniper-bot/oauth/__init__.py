"""OAuth/인증 토큰 관리 — provider 3종."""
from oauth import blogger_oauth, threads_oauth, instagram_oauth

PROVIDERS = {
    "blogger": blogger_oauth,
    "threads": threads_oauth,
    "instagram": instagram_oauth,
}

__all__ = ["blogger_oauth", "threads_oauth", "instagram_oauth", "PROVIDERS"]
