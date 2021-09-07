import typing as t

from .user import User
from .guild import PartialGuild
from .channel import PartialChannel
from .application import PartialApplication

TargetType = t.Literal[1, 2]


class InviteMetadata(t.TypedDict):
    uses: int
    max_uses: int
    max_age: int
    temporary: bool
    created_at: str

class Invite(t.TypedDict, total=False):
    code: str
    guild: t.Optional[PartialGuild]
    channel: PartialChannel
    inviter: t.Optional[User]
    target_type: t.Optional[TargetType]
    target_user: t.Optional[User]
    target_application: t.Optional[PartialApplication]
    approximate_presence_count: t.Optional[int]
    approximate_member_count: t.Optional[int]
    expires_at: t.Optional[str]
    # stage_instance: t.Optional[]
