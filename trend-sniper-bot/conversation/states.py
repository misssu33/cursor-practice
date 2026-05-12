"""ConversationHandler 상태 머신.

Part 2까지 등장하는 상태: INTAKE, CORE_SHEET, FACTCHECK_CLAIM, FACTCHECK_VERDICT.
Part 3/4가 PUBLISH 단계 등을 추가할 수 있어 IntEnum.auto()로 유연하게 둔다.
"""
from __future__ import annotations

from enum import IntEnum, auto


class State(IntEnum):
    IDLE = 0
    INTAKE = auto()
    SCAN = auto()
    CORE_SHEET = auto()
    FACTCHECK_CLAIM = auto()
    FACTCHECK_VERDICT = auto()
    CHANNEL_MENU = auto()
    PUBLISHING = auto()
    # Part 4 — /connect blogger 흐름에서 사용자가 OAuth 코드를 붙여넣을 때까지 대기.
    CONNECT_WAITING_CODE = auto()
