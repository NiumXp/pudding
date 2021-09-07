__all__ = (
    "Channel",
)

import typing as t
from .snowflake import Snowflake

class _RawChannel(t.TypedDict):
    id: Snowflake
    name: str


class _RawGuildChannel(_RawChannel):
    pass


class PartialChannel:
    pass


class Channel(_RawChannel):
    pass
