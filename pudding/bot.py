import asyncio
from typing import NoReturn

from .http import DiscordHTTPClient
from .gateway import DiscordWebSocket


class Bot:
    __slots__ = ("http", "gtws", "loop", "_extensions", "_closed")

    def __init__(self) -> None:
        self.http: DiscordHTTPClient = None
        self.gtws: DiscordWebSocket = None

        self.loop = asyncio.get_event_loop()

        self._extensions = {}
        self._closed = False

    def is_closed(self) -> bool:
        return self._closed

    def load_extension(self, extension: str, /) -> None:
        pass

    def unload_extension(self, extension: str, /) -> None:
        pass

    def reload_extension(self, extension: str, /) -> None:
        pass

    def run(self, token: str):
        pass

    async def start(self) -> None:
        pass

    async def connect(self) -> NoReturn:
        pass

    async def close(self) -> None:
        pass
