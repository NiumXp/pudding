import asyncio
import sys
import zlib
import json
from typing import Any, AnyStr, Callable, Coroutine, Optional, Union

import aiohttp
from aiohttp import WSMsgType as MType

from .gateway import Gateway
from .keep_alive import KeepAlive


class GatewayError(Exception):
    pass


class CloseGateway(Exception):
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
        "_seq",
        "_closed",
        "_buffer",
        "_inflator",
    )

    def __init__(
        self,
        token: str,
        bot=None,
        loop=None,
        # NOTE When the default api version is 8, intents cannot be optional.
        intents: Optional[int] = None,
        gateway: Optional[Gateway] = None,
        session: Optional[aiohttp.ClientSession] = None,
        dispatcher: Optional[Callable[[str, dict], None]] = None,
    ) -> None:

        self.token = token
        self.bot = bot
        self.loop = loop or asyncio.get_event_loop()
        self.intents = intents
        self.gateway = gateway
        self.session = session
        self.dispatcher = dispatcher

        self.socket = None
        self.session_id = None
        self.keep_alive = None
        self._seq = None
        self._closed = False
        self._buffer = bytearray()
        self._inflator = zlib.decompressobj()

    @property
    def latency(self) -> Optional[float]:
        if self.keep_alive:
            return self.keep_alive.latency

    def is_closed(self) -> bool:
        return self._closed

    async def close(self, code) -> None:
        if self._closed:
            raise Exception()

        await self.socket.close(code=code)

        if self.session:
            if (
                not self.bot
                or (self.bot.http.session is not self.session)
            ):
                await self.session.close()

        if self.keep_alive:
            self.keep_alive.stop()

        self.socket = None
        self.session = None
        self.session_id = None
        self.keep_alive: KeepAlive = None
        self._seq = None

        self._closed = True

    async def connect(self) -> None:
        if self.session is None:
            if self.bot:
                self.session = self.bot.http.session
            else:
                self.session = aiohttp.ClientSession()


        if self.gateway is None:
            if self.bot is None:
                raise Exception()

            self.gateway = await self.bot.http.get_bot_gateway()

        self.socket = await self.session.ws_connect(self.gateway.wss)

        await self.poll_event()
        await self.identify()

    async def poll_event(self):
        message = await self.socket.receive(timeout=60)

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
            await self.close(4001)
            print(message)
            raise ReconnectWebSocket()

        # TODO MType.Close
        return

    async def parse_raw_message(self, data: AnyStr) -> dict:
        if type(data) is bytes:
            self._buffer.extend(data)

            if len(data) < 4 or data[-4:] != b'\x00\x00\xff\xff':
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
            interval = d["heartbeat_interval"] / 1000
            self.keep_alive = KeepAlive(self, interval)
            # await self.heartbeat()
            return self.keep_alive.start()

        if op is self.HEARTBEAT_ACK:
            return self.keep_alive.ack()

        if op is self.INVALID_SESSION:
            if d is True:
                await self.close(1000)
                raise ReconnectWebSocket()

            return

        if op is self.RECONNECT:
            await self.close(1000)
            raise ReconnectWebSocket()

        if op is self.DISPATCH:  # 0
            s = payload['s']
            t = payload['t']

            if t == "READY":
                self.session_id = d["session_id"]
                print(payload)
                return

            if t == "RESUMED":
                return

            self._seq = s

            if self.dispatcher:
                self.dispatcher(t, d)

            return

        await self._uknown_payload(payload)

    async def _unkown_payload(self, payload, /):
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
