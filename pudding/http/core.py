from typing import Optional

import aiohttp

from ..gateway import GatewayPayload, GatewayBotPayload


class DiscordHTTPClient:
    __slots__ = (
        "token",

        "session",
        "_closed",
    )

    def __init__(self, token: Optional[str]) -> None:
        self.token = token

        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
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

    async def get_gateway(self) -> GatewayBotPayload:
        return {"url": "wss://gateway.discord.gg/"}  # :D

    async def get_bot_gateway(self) -> GatewayPayload:
        return await self.get_gateway()  # :D
