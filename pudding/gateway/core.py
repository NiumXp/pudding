import asyncio
import sys
import zlib
import json
from typing import Any, AnyStr, Callable, Coroutine, Optional, Union

import aiohttp
from aiohttp import WSMsgType as MType

from .gateway import Gateway
from .keep_alive import KeepAlive

_DEFAULT_INTERVAL = 30


class GatewayError(Exception):
    pass


class CloseGateway(GatewayError):
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message

        super().__init__(f"Gateway closed {code}: {message}")


class ReconnectWebSocket(GatewayError):
    pass


class DiscordWebSocket:
    # https://discord.com/developers/docs/topics/opcodes-and-status-codes
    DISPATCH                = 0
    HEARTBEAT               = 1
    IDENTIFY                = 2
    PRESENCE_UPDATE         = 3
    VOICE_STATE_UPDATE      = 4
    RESUME                  = 6
    RECONNECT               = 7
    REQUEST_GUILD_MEMBERS   = 8
    INVALID_SESSION         = 9
    HELLO                   = 10
    HEARTBEAT_ACK           = 11

    __slots__ = (
        "token",
        "bot",
        "loop",
        "intents",
        "gateway",
        "session",
        "dispatcher",

        "socket",
        "session_id",
        "keep_alive",
        "heartbeat_interval",
        "_seq",
        "_closed",
        "_buffer",
        "_inflator",
    )

    def __init__(
        self,
        token: Optional[str] = None,
        bot=None,
        loop=None,
        # NOTE When the default api version is 8, intents cannot be optional.
        intents: Optional[int] = None,
        gateway: Optional[Gateway] = None,
        session: Optional[aiohttp.ClientSession] = None,
        dispatcher: Optional[Callable[[str, dict], None]] = None,
    ) -> None:

        if token is None:
            if bot is None:
                raise ValueError("bot expected")

            token = bot.token

        self.token = token

        if self.token is None:
            raise ValueError("token expected")

        self.bot = bot
        self.loop = loop or asyncio.get_event_loop()
        self.intents = intents
        self.gateway = gateway
        self.session = session
        self.dispatcher = dispatcher

        if self.intents is None and self.bot:
            self.intents = self.bot.intents

        self.socket = None
        self.session_id = None
        self.keep_alive: KeepAlive = None
        self.heartbeat_interval = _DEFAULT_INTERVAL
        self._seq = None
        self._closed = True
        self._buffer = bytearray()
        self._inflator = zlib.decompressobj()

    @property
    def latency(self) -> Optional[float]:
        if self.keep_alive:
            return self.keep_alive.latency

    def is_closed(self) -> bool:
        return self._closed

    async def close(self, code: Optional[int] = None) -> None:
        if self._closed:
            return

        if code is None:
            code = 4000

        try:
            await self.socket.close(code=code)
        finally:
            self.socket = None

        if self.session:
            if (
                not self.bot
                or (self.bot.http.session is not self.session)
            ):
                if not self.session.closed:
                    await self.session.close()

            self.session = None

        if self.keep_alive:
            self.keep_alive.stop()

        self.session_id = None
        self.keep_alive = None
        self.heartbeat_interval = _DEFAULT_INTERVAL
        self._seq = None
        self._closed = True
        self._buffer = bytearray()

    async def connect(self, resume: bool = False) -> None:
        if self.session is None:
            if self.bot and self.bot.http:
                self.session = self.bot.http.session
            else:
                self.session = aiohttp.ClientSession()

        self.gateway = Gateway("wss://gateway.discord.gg/", version=7)
        if self.gateway is None:
            if self.bot is None or self.bot.http is None:
                raise GatewayError("could not find a Gateway object")

            self.gateway = await self.bot.http.get_bot_gateway()

        self.socket = await self.session.ws_connect(self.gateway.wss)

        await self.poll_event()

        if resume:
            return await self.resume()

        await self.identify()

    async def poll_event(self):
        try:
            timeout = self.heartbeat_interval*2 + 20 
            message = await self.socket.receive(timeout=timeout)
        except asyncio.TimeoutError:
            await self.close()
            raise ReconnectWebSocket() from None

        if message.type is MType.ERROR:
            raise message.error

        if message.type in (MType.TEXT, MType.BINARY):
            if self.keep_alive:
                self.keep_alive.recv()

            payload = await self.parse_raw_message(message.data)
            return await self.handle_payload(payload)

        if message.type is MType.CLOSE:
            code = message.data

            if code not in (1000, 4004, 4010, 4011, 4012, 4013, 4014):
                await self.close()
                raise ReconnectWebSocket()

            raise CloseGateway(code, message.extra)

        if message.type in (MType.CLOSING, MType.CLOSED):
            await self.close()
            raise ReconnectWebSocket()

        await self._unknown_message(message)

    async def _unknown_message(self, message: MType, /) -> None:
        pass

    async def parse_raw_message(self, data: AnyStr) -> dict:
        if type(data) is bytes:
            self._buffer.extend(data)

            if len(data) < 4 or data[-4:] != b'\x00\x00\xff\xff':
                print("returned")
                return

            data = self._inflator.decompress(self._buffer)
            # data = data.decode('utf-8')

            self._buffer.clear()

        # REVIEW Ignoring self.gateway.encoding
        # https://github.com/discord/erlpack
        return json.loads(data)

    async def handle_payload(self, payload: dict) -> None:
        op = int(payload["op"])
        d = payload['d']

        if op is self.HELLO:
            self.heartbeat_interval = d["heartbeat_interval"]

            interval = self.heartbeat_interval / 1000
            self.keep_alive = KeepAlive(self, interval)

            return self.keep_alive.start()

        if op is self.HEARTBEAT_ACK:
            return self.keep_alive.ack()

        if op is self.INVALID_SESSION:
            if d is True:
                await self.close()
                raise ReconnectWebSocket()

            await self.close(1000)
            raise GatewayError("can't reconnect")

        if op is self.RECONNECT:
            await self.close(1000)
            raise ReconnectWebSocket()

        if op is self.DISPATCH:  # 0
            s = payload['s']
            t = payload['t']

            if t == "READY":
                self.session_id = d["session_id"]

            # if t == "RESUMED":
            #     return

            self._seq = s

            if self.dispatcher:
                self.dispatcher(t, d)

            return

        await self._unknown_payload(payload)

    async def _unknown_payload(self, payload, /):
        pass

    def send(self, data: Union[AnyStr, dict]) -> Coroutine[Any, Any, None]:
        if type(data) is bytes:
            return self.socket.send_bytes(data)

        if type(data) is str:
            return self.socket.send_str(data)

        return self.socket.send_json(data)

    # Packets

    def identify(self) -> Coroutine[Any, Any, None]:
        payload = {
            "op": self.IDENTIFY,
            'd': {
                "token": self.token,
                "intents": self.intents,
                "properties": {
                    "$os": sys.platform,
                    "$browser": "pudding",
                    "$device": "pudding",
                },
            },
        }
        return self.send(payload)

    def resume(self) -> Coroutine[Any, Any, None]:
        payload = {
            "op": self.RESUME,
            'd': {
                "seq": self._seq,
                "token": self.token,
                "session_id": self.session_id,
            }
        }
        return self.send(payload)

    def heartbeat(self) -> Coroutine[Any, Any, None]:
        payload = {"op": self.HEARTBEAT,
                   'd': self._seq,}
        return self.send(payload)
