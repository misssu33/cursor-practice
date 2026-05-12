"""SQLAlchemy 엔진/세션 관리 + 초기화 + python -m storage.db 진입점."""
from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import DB_PATH, ensure_dirs
from storage.models import Base


# SQLite 단일 파일. 모든 핸들러는 get_session() 컨텍스트로 접근.
_engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
)
_SessionFactory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False, future=True)


def init_db() -> None:
    """스키마 생성 — idempotent. 부모 디렉터리도 함께 보장."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(_engine)


@contextmanager
def get_session() -> Iterator[Session]:
    """with 블록 안에서 안전한 commit/rollback/close."""
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    # Windows 콘솔(cp949)에서 이모지 깨짐 방지.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, OSError):
        pass

    ensure_dirs()
    init_db()
    print(f"✅ DB 초기화 완료: {DB_PATH}")
