from typing import Callable, Optional

import aiohttp

from ..bot import Bot
from .gateway import Gateway


class DiscordWebSocket:
    __slots__ = (
        "token",
        "bot",
        "intents",
        "gateway",
        "session",
        "dispatcher",

        "socket",
        "_closed",
    )

    def __init__(
        self,
        token: str,
        bot: Optional[Bot] = None,
        intents: Optional[int] = None,
        gateway: Optional[Gateway] = None,
        session: Optional[aiohttp.ClientSession] = None,
        dispatcher: Optional[Callable[[str, dict], None]] = None,
    ) -> None:

        self.token = token
        self.bot = bot
        self.intents = intents
        self.gateway = gateway
        self.session = session
        self.dispatcher = dispatcher

        self.socket = None
        self._closed = False

    def is_closed(self) -> bool:
        return self._closed

    async def close(self) -> None:
        pass

    async def connect(self) -> None:
        pass

    async def poll_event(self) -> bool:
        pass
