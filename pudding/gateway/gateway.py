from typing import TypedDict


class GatewayBotPayload(TypedDict):
    url: str


class SessionStartLimit(TypedDict):
    total: int
    remaining: int
    reset_after: int
    max_concurrency: int


class GatewayPayload(TypedDict):
    url: str
    shards: int
    session_start_limit: SessionStartLimit
