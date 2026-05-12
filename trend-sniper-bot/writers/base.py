"""채널 작성기 공통 베이스 — 코어시트·스캔 결과를 받아 초안 생성."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class WriterInput:
    topic: str
    audience: str
    main_keyword: str
    sub_keywords: list[str]
    goal: str
    tone: str
    differentiation: str
    cta: str
    # 코어시트
    main_message: str
    hooks: list[str]
    data_points: list[str]
    cases: list[str]
    insights: list[str]
    # 팩트체크 통과 데이터 (사용 가능 등급만)
    verified_claims: list[dict] = None
    # 트렌드 인사이트
    related_keywords: list[str] = None


@dataclass
class WriterOutput:
    channel: str
    body: str
    hashtags: list[str]
    char_count: int
    extra: dict       # 인스타 슬라이드 스크립트, 쓰레드 분할 등


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n - 1] + "…"


def _join_hashtags(tags: list[str]) -> str:
    return " ".join(f"#{t.lstrip('#')}" for t in tags if t)


def build_hashtags(main_kw: str, sub_kws: list[str], related: list[str], target_count: int) -> list[str]:
    """메인+서브+연관 키워드로 해시태그 풀 구성."""
    pool: list[str] = []
    seen = set()

    def _add(tag: str):
        tag = tag.strip().replace(" ", "").replace("#", "")
        if tag and tag.lower() not in seen and len(tag) <= 30:
            seen.add(tag.lower())
            pool.append(tag)

    _add(main_kw)
    for kw in sub_kws or []:
        _add(kw)
    for kw in related or []:
        _add(kw)

    # 부족하면 조합형 태그 추가
    if main_kw and len(pool) < target_count:
        for suffix in ["추천", "정리", "가이드", "노하우", "팁", "후기", "비교", "방법"]:
            _add(main_kw + suffix)
            if len(pool) >= target_count:
                break

    return pool[:target_count]
