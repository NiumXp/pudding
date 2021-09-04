import asyncio
import typing as t

from .http import DiscordHTTPClient
from .gateway import DiscordWebSocket
from . import errors, utils


class Bot:
    __slots__ = (
        "intents",

        "loop",
        "http",
        "gtws",
        "token",

        "_extensions",
        "_closed",
    )

    def __init__(self, intents: t.Optional[int] = None) -> None:
        self.intents = intents

        self.loop = asyncio.get_event_loop()
        self.http: DiscordHTTPClient = DiscordHTTPClient()
        self.gtws: t.Optional[DiscordWebSocket] = None
        self.token: t.Optional[str] = None

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

    def run(self, token: str) -> None:
        self.token = token

        async def runner() -> None:
            try:
                await self.start()
                await self.connect()
            finally:
                if not self.is_closed():
                    await self.close()

        future = asyncio.ensure_future(runner(), loop=self.loop)
        future.add_done_callback(lambda _: self.loop.stop())

        with utils.suppress_all():
            self.loop.run_forever()

        if not future.cancelled():
            return future.result()

    async def start(self) -> None:
        """Creates a `DiscordHTTPClient` session."""
        self.http = DiscordHTTPClient(self.token)

    async def connect(self) -> t.NoReturn:
        """Creates a `DiscordWebSocket` connection."""
        gateway = await self.http.get_bot_gateway()

        self.gtws = DiscordWebSocket(
            token=self.token,
            intents=self.intents,
            gateway=gateway,
            dispatcher=self._dispatcher,
        )

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

        with utils.suppress_all():
            await self.http.close()

        if self.gtws:
            await self.gtws.close()

        self._closed = True
