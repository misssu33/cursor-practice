"""팩트체크 판정 등급 (사용자가 수동 선택 — A안)."""
from enum import Enum


class Verdict(str, Enum):
    TRUE = "TRUE"
    MOSTLY_TRUE = "MOSTLY_TRUE"
    HALF_TRUE = "HALF_TRUE"
    MOSTLY_FALSE = "MOSTLY_FALSE"
    FALSE = "FALSE"
    UNVERIFIABLE = "UNVERIFIABLE"
    OUTDATED = "OUTDATED"
    MISLEADING = "MISLEADING"


VERDICT_LABELS = {
    Verdict.TRUE:          "✅ TRUE (사실)",
    Verdict.MOSTLY_TRUE:   "🟢 MOSTLY TRUE (대체로 사실)",
    Verdict.HALF_TRUE:     "🟡 HALF TRUE (절반의 진실)",
    Verdict.MOSTLY_FALSE:  "🟠 MOSTLY FALSE (대체로 거짓)",
    Verdict.FALSE:         "🔴 FALSE (거짓)",
    Verdict.UNVERIFIABLE:  "⚪ UNVERIFIABLE (검증불가)",
    Verdict.OUTDATED:      "🕰️ OUTDATED (낡은 정보)",
    Verdict.MISLEADING:    "⚠️ MISLEADING (오도)",
}


def all_verdicts() -> list[tuple[str, str]]:
    return [(v.value, VERDICT_LABELS[v]) for v in Verdict]


def is_usable(verdict: str) -> bool:
    """콘텐츠에 사용 가능한 판정인지."""
    return verdict in (Verdict.TRUE.value, Verdict.MOSTLY_TRUE.value)
