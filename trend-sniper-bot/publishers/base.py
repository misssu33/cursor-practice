"""발행자 공통 베이스."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PublishResult:
    ok: bool
    url: Optional[str] = None
    error: Optional[str] = None
    raw: Optional[dict] = None
