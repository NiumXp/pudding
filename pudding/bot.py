import asyncio
from typing import NoReturn, Optional

from .http import DiscordHTTPClient
from .gateway import DiscordWebSocket
from . import errors


class Bot:
    __slots__ = (
        "intents",

        "http",
        "gtws",
        "loop",
        "token",
        "_extensions",
        "_closed",
    )

    def __init__(self, intents: Optional[int] = None) -> None:
        self.intents = intents

        self.http: DiscordHTTPClient = None
        self.gtws: DiscordWebSocket = None
        self.loop = asyncio.get_event_loop()
        self.token = None

        self._extensions = {}
        self._closed = True

    def is_closed(self) -> bool:
        return self._closed

    def load_extension(self, extension: str, /) -> None:
        pass

    def unload_extension(self, extension: str, /) -> None:
        pass

    def reload_extension(self, extension: str, /) -> None:
        pass

    def run(self, token: str):
        self.token = token

        async def runner() -> None:
            try:
                await self.start()
                await self.connect()
            finally:
                if not self.is_closed():
                    await self.close()

        future = asyncio.ensure_future(runner(), loop=self.loop)

        try:
            self.loop.run_forever()
        finally:
            pass

        if not future.cancelled():
            return future.result()

    async def start(self) -> None:
        """Creates a `DiscordHTTPClient` session."""
        self.http = DiscordHTTPClient(self.token)

    async def connect(self) -> NoReturn:
        """Creates a `DiscordWebSocket` connection."""
        gt = await self.http.get_bot_gateway()

        self.gtws = DiscordWebSocket(token=self.token, intents=self.intents,
                                     gateway=gt, dispatcher=self._dispatcher)

        await self.gtws.connect()

        while True:
            try:
                await self.gtws.poll_event()
            except errors.ReconnectWebSocket:
                await self.gtws.connect(resume=True)

    def _dispatcher(self, name: str, payload: dict) -> None:
        print(name, len(payload))

    async def close(self) -> None:
        if self._closed:
            return

        try:
            await self.http.close()
        finally:
            self.http = None

        try:
            await self.gtws.close()
        finally:
            self.gtws = None

        self._closed = True
