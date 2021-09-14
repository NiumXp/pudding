import typing as t
from .snowflake import Snowflake


class VoiceRegion(t.TypedDict):
    id: Snowflake
    name: str
    vip: bool
    optimal: bool
    deprecated: bool
    custom: bool
