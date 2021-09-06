import typing as t
from .user import User
from .snowflake import Snowflake


class PartialEmoji(t.TypedDict):
    id: t.Optional[Snowflake]
    name: t.Optional[str]


class Emoji(PartialEmoji, total=False):
    roles: t.Optional[t.List[Snowflake]]
    user: t.Optional[User]
    require_colons: t.Optional[bool]
    managed: t.Optional[bool]
    animated: t.Optional[bool]
    available: t.Optional[bool]
