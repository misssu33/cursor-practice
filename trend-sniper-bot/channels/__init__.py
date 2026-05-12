"""채널 추상·사양 — 외부 노출 API."""
from channels.base import (
    Channel, ChannelSpec, PublishResult, PublishMode,
    SPECS, get_channel, list_channels,
)

__all__ = [
    "Channel", "ChannelSpec", "PublishResult", "PublishMode",
    "SPECS", "get_channel", "list_channels",
]
