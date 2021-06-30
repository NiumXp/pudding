from typing import Optional

from ..gateway import Gateway


class DiscordHTTPClient:
    __slots__ = ("token", "session",)

    def __init__(self, token: Optional[str]) -> None:
        self.token = token

        self.session = None

    async def request(self, method: str, endpoint: str, **parameters):
        pass

    async def get_gateway(self) -> Gateway:
        pass

    async def get_bot_gatewat(self) -> Gateway:
        pass
