import typing as t
from .snowflake import Snowflake

PremiumType = t.Literal[0, 1, 2]


class PartialUser(t.TypedDict):
    id: Snowflake
    username: str
    discriminator: str
    avatar: t.Optional[str]


class User(PartialUser, total=False):
    bot: t.Optional[bool]
    bio: t.Optional[str]  # not documented (only bots)
    system: t.Optional[bool]
    mfa_enabled: t.Optional[bool]
    local: t.Optional[str]
    verified: t.Optional[bool]
    email: t.Optional[str]
    flags: t.Optional[int]
    premium_type: t.Optional[PremiumType]
    public_flags: t.Optional[int]
