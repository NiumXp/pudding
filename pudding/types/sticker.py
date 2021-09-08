import typing as t

from .user import User
from .snowflake import Snowflake

StickerType = t.Literal[1, 2]
StickerFormatType = t.Literal[1, 2, 3]


class _OptionalSticker(t.TypedDict, total=False):
    pack_id: t.Optional[Snowflake]
    available: t.Optional[bool]
    guild_id: t.Optional[Snowflake]
    user: t.Optional[User]
    sort_value: t.Optional[int]


class Sticker(_OptionalSticker):
    id: Snowflake
    name: str
    description: t.Optional[str]
    tags: str
    asset: t.Literal['']  # deprecated
    type: StickerType
    format_type: StickerFormatType
