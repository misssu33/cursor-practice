"""인증 — config.ALLOWED_USER_IDS 에 등록된 사용자만 봇을 사용한다."""
from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable

import config


def is_allowed(user_id: int) -> bool:
    """ALLOWED_USER_IDS 에 포함되어야 통과. 빈 리스트면 모두 차단."""
    return bool(config.ALLOWED_USER_IDS) and user_id in config.ALLOWED_USER_IDS


def require_auth(handler: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """python-telegram-bot 핸들러용 데코레이터.

    - update.effective_user.id 를 ALLOWED_USER_IDS 와 대조
    - 미허용 시 짧은 거절 메시지 응답 후 None 반환 (ConversationHandler가 상태 유지)
    """

    @wraps(handler)
    async def wrapper(update, context, *args, **kwargs):  # type: ignore[no-untyped-def]
        uid = update.effective_user.id if getattr(update, "effective_user", None) else 0
        if not is_allowed(uid):
            target = getattr(update, "message", None) or getattr(update, "callback_query", None)
            if target is not None:
                # message 와 callback_query 둘 다 reply_text 또는 answer 인터페이스
                reply = getattr(target, "reply_text", None)
                if reply:
                    await reply("⛔ 권한이 없습니다.")
            return None
        return await handler(update, context, *args, **kwargs)

    return wrapper
