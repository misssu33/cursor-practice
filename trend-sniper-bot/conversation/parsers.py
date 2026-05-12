"""사용자 입력 파서 — 인테이크 양식 + 코어시트 양식."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


# ───────────────── 인테이크 양식 ─────────────────

# 라벨 → 표준 필드. 한글·영문 모두 허용.
_INTAKE_ALIASES: dict[str, set[str]] = {
    "topic":           {"주제", "topic"},
    "audience":        {"타깃", "타겟", "audience", "target"},
    "main_keyword":    {"메인키워드", "메인 키워드", "main keyword", "main_keyword", "키워드"},
    "sub_keywords":    {"서브키워드", "서브 키워드", "sub_keywords", "sub keywords", "보조키워드"},
    "goal":            {"목표", "goal", "objective"},
    "tone":            {"톤", "어투", "tone"},
    "publish_at":      {"발행시점", "발행 시점", "발행일", "publish_at", "발행", "일정"},
    "differentiation": {"차별화", "differentiation"},
    "cta":             {"cta", "콜투액션", "행동유도"},
}
_INTAKE_REQUIRED = ("topic", "audience", "main_keyword", "goal", "tone", "publish_at")


@dataclass(frozen=True)
class IntakeForm:
    """`/new` 한 번에 받는 인테이크 양식 9필드."""
    topic: str
    audience: str
    main_keyword: str
    sub_keywords: list[str]
    goal: str
    tone: str
    publish_at: str
    differentiation: str = ""
    cta: str = ""


def _norm_key(raw: str) -> str | None:
    """라벨 문자열을 표준 키로 변환. 알 수 없으면 None."""
    k = raw.strip().lower().replace(" ", "")
    for canonical, aliases in _INTAKE_ALIASES.items():
        if k == canonical:
            return canonical
        for alias in aliases:
            if k == alias.lower().replace(" ", ""):
                return canonical
    return None


def _split_sub_keywords(value: str) -> list[str]:
    """쉼표·슬래시·세미콜론 모두 허용. 공백·중복 제거."""
    parts = re.split(r"[,/;\n]+", value)
    out: list[str] = []
    for p in parts:
        s = p.strip().lstrip("-•").strip()
        if s and s not in out:
            out.append(s)
    return out


def parse_intake_form(text: str | None) -> IntakeForm | None:
    """인테이크 양식 텍스트를 파싱한다. 필수 항목이 비면 None."""
    if not text or not text.strip():
        return None

    fields: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("*").strip()
        if not line or ":" not in line:
            continue
        key_raw, _, value = line.partition(":")
        canonical = _norm_key(key_raw)
        if canonical is None:
            continue
        fields[canonical] = value.strip()

    for key in _INTAKE_REQUIRED:
        if not fields.get(key):
            return None

    sub_kw = _split_sub_keywords(fields.get("sub_keywords", ""))

    return IntakeForm(
        topic=fields["topic"],
        audience=fields["audience"],
        main_keyword=fields["main_keyword"],
        sub_keywords=sub_kw,
        goal=fields["goal"],
        tone=fields["tone"],
        publish_at=fields["publish_at"],
        differentiation=fields.get("differentiation", ""),
        cta=fields.get("cta", ""),
    )


# 사용자 가이드 호환 별칭
parse_form = parse_intake_form


# ───────────────── 코어시트 양식 ─────────────────

_CORE_SECTIONS: dict[str, set[str]] = {
    "main_message": {"메인메시지", "메인 메시지", "main_message", "main message"},
    "hooks":        {"후킹", "hooks", "hook"},
    "data_points":  {"데이터", "data", "data_points", "수치"},
    "cases":        {"사례", "cases", "case"},
    "insights":     {"인사이트", "insights", "insight"},
}


@dataclass
class CoreSheet:
    """`/core` 입력 결과. 모든 리스트 필드는 빈 리스트가 기본값."""
    main_message: str = ""
    hooks: list[str] = field(default_factory=list)
    data_points: list[str] = field(default_factory=list)
    cases: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)


def _match_section(line: str) -> str | None:
    """'후킹:' 같은 섹션 헤더 라인 → 표준 키."""
    if ":" not in line:
        return None
    head = line.split(":", 1)[0].strip().lower().replace(" ", "")
    for canonical, aliases in _CORE_SECTIONS.items():
        if head == canonical:
            return canonical
        for alias in aliases:
            if head == alias.lower().replace(" ", ""):
                return canonical
    return None


def _bullet(line: str) -> str | None:
    """'- 항목' / '• 항목' / '1. 항목' 형식에서 본문만 추출. 본문이 비면 None."""
    s = line.strip()
    if not s:
        return None
    m = re.match(r"^[-•*]\s*(.+)$", s)
    if m:
        return m.group(1).strip() or None
    m = re.match(r"^\d+[.)]\s*(.+)$", s)
    if m:
        return m.group(1).strip() or None
    return None


def parse_core_sheet(text: str | None) -> CoreSheet | None:
    """코어시트 양식 텍스트를 파싱한다. 메인메시지 누락 시 None."""
    if not text or not text.strip():
        return None

    sheet = CoreSheet()
    current_section: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            current_section = None
            continue

        section = _match_section(line)
        if section is not None:
            # 'main_message: ...' 처럼 같은 줄에 값이 있을 수도 있음
            _, _, inline_value = line.partition(":")
            inline_value = inline_value.strip()
            if section == "main_message":
                sheet.main_message = inline_value
                current_section = None
            else:
                current_section = section
                if inline_value:
                    _append(sheet, section, inline_value)
            continue

        # 섹션 안의 불릿
        if current_section is not None:
            value = _bullet(line) or line
            _append(sheet, current_section, value)

    if not sheet.main_message:
        return None
    return sheet


def _append(sheet: CoreSheet, section: str, value: str) -> None:
    """현재 섹션의 리스트에 한 항목 추가."""
    bucket: list[str] = getattr(sheet, section)
    if value and value not in bucket:
        bucket.append(value)
