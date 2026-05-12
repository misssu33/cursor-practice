"""SQLAlchemy 2.x 선언형 모델 — Part 2까지 등장하는 모든 도메인 객체."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import ForeignKey, JSON, String, Text, DateTime, Integer, Index, Boolean
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
    contents: Mapped[list["ChannelContent"]] = relationship(
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


class ChannelContent(Base):
    """프로젝트별·채널별 1행의 작성 결과 (writer 초안 + SEO 점수).

    status 흐름: draft (SEO 미달) → ready (SEO 합격 또는 사용자 승인) → published / failed (Part 4)
    프로젝트 × 채널의 단일성은 channel_handler 에서 query→upsert 로 보장.
    DB 레벨 UniqueConstraint 는 Part 4 마이그레이션에서 추가 예정.
    """
    __tablename__ = "channel_contents"
    __table_args__ = (
        Index("ix_channel_contents_project_channel", "project_id", "channel"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True,
    )
    channel: Mapped[str] = mapped_column(String(40), nullable=False)  # linkedin|naver|adsense|instagram|threads
    body: Mapped[str] = mapped_column(Text, default="")
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    seo_score: Mapped[int] = mapped_column(Integer, default=0)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    # Part 4 에서 사용할 발행 URL/시각 — 지금은 비워둠.
    published_url: Mapped[str] = mapped_column(String(500), default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    project: Mapped["Project"] = relationship(back_populates="contents")
    instagram_images: Mapped[list["InstagramImage"]] = relationship(
        back_populates="content", cascade="all, delete-orphan",
    )


class InstagramImage(Base):
    """인스타 슬라이드 이미지 — 한 슬라이드당 1행. upload_mode 로 A(single)/B(group) 식별.

    텔레그램의 media_group_id 는 인스타 발행 API 가 사용하지 않으므로 DB 저장하지 않는다.
    슬라이드 순서가 필요한 곳에서는 .order_by(InstagramImage.seq) 로 정렬해 쿼리한다.
    """
    __tablename__ = "instagram_images"
    __table_args__ = (Index("ix_instagram_images_content_seq", "content_id", "seq"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content_id: Mapped[int] = mapped_column(
        ForeignKey("channel_contents.id", ondelete="CASCADE"), index=True,
    )
    seq: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    local_path: Mapped[str] = mapped_column(String(500), default="")
    cloud_url: Mapped[str] = mapped_column(String(500), default="")
    # 'single' (A안 — 단일 사진) 또는 'group' (B안 — 미디어그룹 묶음)
    upload_mode: Mapped[str] = mapped_column(String(20), default="single")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    content: Mapped["ChannelContent"] = relationship(back_populates="instagram_images")


class OAuthToken(Base):
    """provider 별 OAuth 토큰 — Part 4 발행 단계에서 사용.

    (user_id, provider) 가 사실상 PK 역할 — 동일 사용자가 같은 provider 를 두 번 연결하면 upsert.
    Blogger 는 refresh_token + expires_at 으로 자동 갱신. Threads / Instagram 은 .env 장기 토큰.
    """
    __tablename__ = "oauth_tokens"
    __table_args__ = (
        Index("uq_oauth_tokens_user_provider", "user_id", "provider", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Schedule(Base):
    """발행 스케줄 1건 — `(project_id, channel)` 당 1행. APScheduler 잡과 1:1 대응.

    프로세스 재시작 시 APScheduler 메모리는 비어 있으나, 이 행은 DB 에 남아 다음 부팅 시 재등록할 수 있다.
    (현 범위 밖이므로 자동 재등록은 구현하지 않는다 — 사용자 가이드의 알려진 한계 4번 참조)
    """
    __tablename__ = "schedules"
    __table_args__ = (
        Index("ix_schedules_project_channel", "project_id", "channel"),
        Index("ix_schedules_publish_at", "publish_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True,
    )
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    publish_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    publish_mode: Mapped[str] = mapped_column(String(20), default="manual")
    reminded: Mapped[bool] = mapped_column(Boolean, default=False)
    executed: Mapped[bool] = mapped_column(Boolean, default=False)
    result: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
