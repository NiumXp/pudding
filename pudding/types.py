import typing as t


class GatewayPayload(t.TypedDict):
    url: str


class SessionStartLimit(t.TypedDict):
    total: int
    remaining: int
    reset_after: int
    max_concurrency: int


class GatewayBotPayload(t.TypedDict):
    url: str
    shards: int
    session_start_limit: SessionStartLimit


class Packet(t.TypedDict):
    op: t.Union[int, str]
    d: t.Any


class Payload(t.TypedDict):
    op: t.Union[int, str]
    d: t.Any
    s: t.Union[int, None]
    t: str


class Channel(t.TypedDict, total=False):
    ...
