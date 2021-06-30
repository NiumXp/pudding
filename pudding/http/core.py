from typing import Optional

import aiohttp

from ..gateway import Gateway


class DiscordHTTPClient:
    __slots__ = (
        "token",

        "session",
        "_closed",
    )

    def __init__(self, token: Optional[str]) -> None:
        self.token = token

        self.session: aiohttp.ClientSession = None
        self._closed = True

    def is_closed(self) -> bool:
        return self._closed

    async def close(self) -> None:
        if self._closed:
            return

        try:
            await self.session.close()
        finally:
            self.session = None

        self._closed = True

    async def request(self, method: str, endpoint: str, **parameters):
        pass

    async def get_gateway(self) -> Gateway:
        pass

    async def get_bot_gatewat(self) -> Gateway:
        pass