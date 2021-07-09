from typing import Optional, TypedDict


class SessionStartLimit(TypedDict):
    total: int
    remaining: int
    reset_after: int
    max_concurrency: int


class GatewayPayload(TypedDict):
    url: str
    shards: Optional[int]
    session_start_limit: Optional[SessionStartLimit]
