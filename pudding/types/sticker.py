import typing as t

from .user import User
from .snowflake import Snowflake

StickerType = t.Literal[1, 2]
StickerFormatType = t.Literal[1, 2, 3]


class PartialSticker(t.TypedDict):
    id: Snowflake
    name: str
    format_type: StickerFormatType


class _OptionalSticker(t.TypedDict, total=False):
    pack_id: t.Optional[Snowflake]
    available: t.Optional[bool]
    guild_id: t.Optional[Snowflake]
    user: t.Optional[User]
    sort_value: t.Optional[int]


class Sticker(_OptionalSticker, PartialSticker):
    description: t.Optional[str]
    tags: str
    asset: t.Literal['']  # deprecated
    type: StickerType


class StickerPack(t.TypedDict):
    id: Snowflake
    stickers: t.List[Sticker]
    name: str
    sku_id: Snowflake
    cover_sticker_id: t.Optional[Snowflake]
    description: str
    banner_asset_id: Snowflake
