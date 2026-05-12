"""SQLAlchemy 2.x 선언형 모델 — Part 2까지 등장하는 모든 도메인 객체."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import ForeignKey, JSON, String, Text, DateTime, Integer, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    """타임스탬프 — UTC. SQLite TEXT 직렬화 시 ISO 형식."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    """모든 모델의 베이스."""


class Project(Base):
    """사용자의 한 콘텐츠 프로젝트.

    상태(status) 흐름: intake → scanned → core → factcheck_done/skipped → publishing → published
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # 인테이크 양식 9필드
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    audience: Mapped[str] = mapped_column(String(200), default="")
    main_keyword: Mapped[str] = mapped_column(String(120), default="", index=True)
    # 서브 키워드는 list → JSON 컬럼
    sub_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    goal: Mapped[str] = mapped_column(Text, default="")
    tone: Mapped[str] = mapped_column(String(80), default="")
    publish_at: Mapped[str] = mapped_column(String(80), default="")
    differentiation: Mapped[str] = mapped_column(Text, default="")
    cta: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[str] = mapped_column(String(40), default="intake", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    # 관계 — cascade로 자식까지 삭제
    trend_scans: Mapped[list["TrendScan"]] = relationship(
        back_populates="project", cascade="all, delete-orphan",
    )
    core_sheet: Mapped["CoreSheetRow | None"] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False,
    )
    factchecks: Mapped[list["FactCheck"]] = relationship(
        back_populates="project", cascade="all, delete-orphan",
    )


class TrendScan(Base):
    """트렌드 스캔 결과 — 소스별 1행. payload는 JSON(list 또는 dict)."""
    __tablename__ = "trend_scans"
    __table_args__ = (Index("ix_trend_scans_project_source", "project_id", "source"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    # autocomplete | naver_news | naver_blog | youtube | trends | rss | insights
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[Any] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    project: Mapped["Project"] = relationship(back_populates="trend_scans")


class CoreSheetRow(Base):
    """프로젝트당 1행의 코어시트 — 5개 영역 모두 리스트(JSON)."""
    __tablename__ = "core_sheets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True,
    )

    main_message: Mapped[str] = mapped_column(Text, default="")
    hooks: Mapped[list[str]] = mapped_column(JSON, default=list)
    data_points: Mapped[list[str]] = mapped_column(JSON, default=list)
    cases: Mapped[list[str]] = mapped_column(JSON, default=list)
    insights: Mapped[list[str]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    project: Mapped["Project"] = relationship(back_populates="core_sheet")


class FactCheck(Base):
    """팩트체크 결과 — 사용자가 수동 판정한 verdict 와 자료(sources)를 함께 저장."""
    __tablename__ = "factchecks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True,
    )
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[dict]] = mapped_column(JSON, default=list)
    verdict: Mapped[str] = mapped_column(String(40), default="UNVERIFIABLE")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    project: Mapped["Project"] = relationship(back_populates="factchecks")
