"""채널 추상 + 사양 + 등록소.

Part 2의 validators.seo_scorer는 `get_channel(key) → ChannelSpec`을 호출하고
ChannelSpec의 `min_len`/`max_len`/`hashtag_min`/`hashtag_max`만 읽는다.
Part 3 의 writers 는 동일하게 spec 만 참조.
Part 4 의 publishers.dispatcher / exporters / scheduler 가 `publish_mode` / `use_markdown` 을 추가로 참조.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class PublishMode(str, Enum):
    """채널별 발행 흐름.

    - AUTO       : 봇이 API 로 직접 발행 (Threads / Blogger).
    - SEMI_AUTO  : 봇이 API 호출하지만 사전 준비물 필요 (Instagram → Cloudinary URL 필수).
    - MANUAL     : 봇은 본문만 제공, 사용자가 직접 발행 후 ✅ 버튼으로 보고 (LinkedIn / Naver).
    """
    AUTO = "auto"
    SEMI_AUTO = "semi"
    MANUAL = "manual"


@dataclass(frozen=True)
class ChannelSpec:
    """채널 작성 규약 — 분량·해시태그·톤·형식 + 발행 모드 힌트."""
    key: str            # linkedin | naver | adsense | instagram | threads
    name: str           # 사람이 읽는 이름
    min_len: int        # 본문 최소 글자수
    max_len: int        # 본문 권장 최대 글자수
    hashtag_min: int
    hashtag_max: int
    tone_hint: str
    body_format: str
    # Part 4 — 발행 모드.
    publish_mode: PublishMode = PublishMode.MANUAL
    # exporters 가 .md / .txt 확장자 선택 시 참조. 마크다운 헤더 사용 채널만 True.
    use_markdown: bool = False


@dataclass
class PublishResult:
    """publish() 호출 결과."""
    ok: bool
    post_id: str = ""
    url: str = ""
    error: str = ""


# Part 3에서 ThreadsChannel / BloggerChannel 등이 상속.
class Channel(ABC):
    spec: ChannelSpec

    @abstractmethod
    def publish(self, *, title: str, body: str, **kwargs) -> PublishResult: ...

    @abstractmethod
    def is_configured(self) -> bool: ...


# 5개 채널 사양 — seo_scorer 가 참조하는 핵심 값들 + Part 4 발행 모드.
SPECS: dict[str, ChannelSpec] = {
    "linkedin": ChannelSpec(
        key="linkedin", name="LinkedIn",
        min_len=800, max_len=2000,
        hashtag_min=3, hashtag_max=5,
        tone_hint="전문성·통찰 강조. 1인칭 경험 + 데이터 인용 + 마무리 질문(CTA).",
        body_format="짧은 단락(2~4줄), 줄바꿈으로 호흡 만들기. 해시태그는 본문 끝.",
        publish_mode=PublishMode.MANUAL,
        use_markdown=False,
    ),
    "naver": ChannelSpec(
        key="naver", name="네이버 블로그",
        min_len=1200, max_len=2500,
        hashtag_min=5, hashtag_max=15,
        tone_hint="친근·구어체. 정보 정확성 유지. 마크다운 헤더 금지(스마트에디터 호환).",
        body_format="제목/도입/본문/마무리. 이미지 자리(<이미지: ...>) 표시 권장.",
        publish_mode=PublishMode.MANUAL,
        use_markdown=False,
    ),
    "adsense": ChannelSpec(
        key="adsense", name="애드센스 블로그",
        min_len=2500, max_len=6000,
        hashtag_min=5, hashtag_max=10,
        tone_hint="정보 정확성·E-E-A-T. 출처 명시, FAQ로 마무리.",
        body_format="H2(## 1.) / H3(### 1-1.) 번호 헤더 + FAQ 섹션 필수.",
        publish_mode=PublishMode.AUTO,
        use_markdown=True,
    ),
    "instagram": ChannelSpec(
        key="instagram", name="Instagram 캐러셀",
        min_len=200, max_len=2200,
        hashtag_min=8, hashtag_max=30,
        tone_hint="감성·시각 중심. 첫 줄로 시선 잡기.",
        body_format="캡션 + 슬라이드별 텍스트(<슬라이드 1: ...> 형식).",
        publish_mode=PublishMode.SEMI_AUTO,
        use_markdown=False,
    ),
    "threads": ChannelSpec(
        key="threads", name="Threads",
        min_len=300, max_len=2500,
        hashtag_min=2, hashtag_max=3,
        tone_hint="단문·구어체. 첫 포스트로 후킹, 마지막 포스트로 CTA.",
        body_format="5개 포스트로 분할(각 500자 이하). 구분자 `\\n---\\n` 사용.",
        publish_mode=PublishMode.AUTO,
        use_markdown=False,
    ),
}


def get_channel(key: str) -> ChannelSpec:
    """채널 식별자로 spec 조회. 미등록이면 KeyError."""
    if not key:
        raise KeyError("채널 키가 비어 있습니다.")
    return SPECS[key.strip().lower()]


def list_channels() -> list[str]:
    return sorted(SPECS.keys())
