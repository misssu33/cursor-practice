"""중앙 로깅 설정 — 콘솔 + 회전 파일."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import config


_INITIALIZED = False


def _ensure_init() -> None:
    """루트 로거에 핸들러를 한 번만 부착."""
    global _INITIALIZED
    if _INITIALIZED:
        return

    Path(config.LOG_PATH).parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(config.LOG_LEVEL)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)

    fh = RotatingFileHandler(
        config.LOG_PATH, maxBytes=2_000_000, backupCount=3, encoding="utf-8",
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)

    _INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """이름 있는 자식 로거 — 호출자 모듈별로 사용."""
    _ensure_init()
    return logging.getLogger(name)
