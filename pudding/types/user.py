import typing as t
from .snowflake import Snowflake

PremiumType = t.Literal[0, 1, 2]


class BaseUser(t.TypedDict):
    id: Snowflake
    username: str
    discriminator: str
    avatar: t.Optional[str]


class User(BaseUser, total=False):
    bot: t.Optional[bool]
    system: t.Optional[bool]
    mfa_enabled: t.Optional[bool]
    local: t.Optional[str]
    verified: t.Optional[bool]
    email: t.Optional[str]
    flags: t.Optional[int]
    premium_type: t.Optional[PremiumType]
    public_flags: t.Optional[int]
