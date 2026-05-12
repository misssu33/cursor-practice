"""텔레그램 헬퍼 — Markdown 전송·키보드 빌더·MarkdownV2 escape."""
from __future__ import annotations

from typing import Iterable

try:
    from telegram import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        KeyboardButton,
        ReplyKeyboardMarkup,
        Update,
    )
except ImportError:
    InlineKeyboardButton = None  # type: ignore[assignment]
    InlineKeyboardMarkup = None  # type: ignore[assignment]
    KeyboardButton = None  # type: ignore[assignment]
    ReplyKeyboardMarkup = None  # type: ignore[assignment]
    Update = None  # type: ignore[assignment]


async def send_md(update, text: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
    """Markdown 모드로 메시지를 전송한다. update.message 가 있으면 reply_text, 없으면 chat 으로 전송.

    파싱 실패(잘못된 마크다운) 시 평문으로 폴백.
    """
    bot = getattr(getattr(update, "_bot", None), "send_message", None)
    target = getattr(update, "message", None)

    async def _reply(t: str, **kw):  # type: ignore[no-untyped-def]
        if target is not None:
            return await target.reply_text(t, **kw)
        chat_id = getattr(getattr(update, "effective_chat", None), "id", None)
        if chat_id is None:
            return None
        from telegram.ext import Application  # noqa: F401  (의존성 체크)
        # context.bot 없이 호출되는 경우는 거의 없지만, 안전을 위해 raw send_message 시도
        if bot is None:
            return None
        return await bot(chat_id=chat_id, text=t, **kw)

    try:
        await _reply(text, parse_mode="Markdown", **kwargs)
    except Exception:
        # 마크다운 파싱 실패 시 평문 폴백
        await _reply(text, **kwargs)


_MD_V2_SPECIAL = set(r"_*[]()~`>#+-=|{}.!")


def escape_md_v2(text: str) -> str:
    """텔레그램 MarkdownV2 특수문자 escape."""
    out: list[str] = []
    for ch in text or "":
        if ch in _MD_V2_SPECIAL:
            out.append("\\")
        out.append(ch)
    return "".join(out)


def chunk(items: list, cols: int) -> list[list]:
    cols = max(1, int(cols))
    return [items[i:i + cols] for i in range(0, len(items), cols)]


def inline_buttons(items: Iterable[tuple[str, str]], cols: int = 2):
    if InlineKeyboardButton is None:
        raise RuntimeError("python-telegram-bot 미설치")
    btns = [InlineKeyboardButton(label, callback_data=data) for label, data in items]
    return InlineKeyboardMarkup(chunk(btns, cols))


def reply_buttons(labels: Iterable[str], cols: int = 2, one_time: bool = True):
    if KeyboardButton is None:
        raise RuntimeError("python-telegram-bot 미설치")
    btns = [KeyboardButton(label) for label in labels]
    return ReplyKeyboardMarkup(
        chunk(btns, cols),
        resize_keyboard=True,
        one_time_keyboard=one_time,
    )
