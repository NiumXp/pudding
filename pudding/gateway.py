import sys
import zlib
import json
import time
import asyncio
import threading
import traceback
import typing as t
from urllib.parse import urlencode
from asyncio.events import AbstractEventLoop

import aiohttp
from aiohttp import WSMsgType as MType
from aiohttp.http_websocket import WSMessage

from . import errors
from .types import GatewayBotPayload, Packet, Payload, GatewayPayload

_DEFAULT_INTERVAL = 30


class KeepAlive(threading.Thread):
    __slots__ = (
        "ws",
        "interval",

        "latency",
        "_event",
        "_last_ack",
        "_last_send",
        "_last_recv",
    )

    def __init__(self, ws: "DiscordWebSocket", interval: int, **kwargs: t.Any) -> None:
        self.ws = ws
        self.interval = interval

        super().__init__(daemon=True, **kwargs)

        self.latency = None
        self._event = threading.Event()
        self._last_ack = time.perf_counter()
        self._last_send = time.perf_counter()
        self._last_recv = time.perf_counter()

    def run(self) -> None:
        while not self._event.wait(self.interval):
            if self._last_ack + (self.interval*1.5) < time.perf_counter():
                coro = self.ws.close()
                future = asyncio.run_coroutine_threadsafe(coro, self.ws.loop)

                try:
                    future.result()
                finally:
                    return self.stop()

            coro = self.send_heartbeat_packet()
            future = asyncio.run_coroutine_threadsafe(coro, self.ws.loop)

            try:
                future.result()
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                return self.stop()

    def send_heartbeat_packet(self) -> t.Coroutine[t.Any, t.Any, None]:
        packet = self.ws.heartbeat()

        async def send():
            await self.ws.send(packet)
            self.send()

        return send()

    def stop(self) -> None:
        if not self._event.is_set():
            self._event.set()

    def ack(self) -> None:
        now = time.perf_counter()
        self.latency = now - self._last_send
        self._last_ack = now

    def recv(self) -> None:
        self._last_recv = time.perf_counter()

    def send(self) -> None:
        self._last_send = time.perf_counter()


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

    _VERSION = 9

    __slots__ = (
        "token",
        "intents",
        "gateway",
        "dispatcher",
        "loop",
        "session",

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
        token: str,
        intents: int,
        gateway: t.Union[GatewayPayload, GatewayBotPayload],
        dispatcher: t.Callable[[str, t.Any], None],
        loop: t.Optional[AbstractEventLoop] = None,
        session: t.Optional[aiohttp.ClientSession] = None,
    ) -> None:

        self.token = token
        self.intents = intents
        self.gateway = gateway
        self.dispatcher = dispatcher
        self.loop = loop or asyncio.get_event_loop()
        self.session = session

        self.socket = None
        self.session_id: t.Optional[int] = None
        self.keep_alive: t.Optional[KeepAlive] = None
        self.heartbeat_interval = _DEFAULT_INTERVAL
        self._seq: t.Optional[int] = None
        self._closed = True
        self._buffer = bytearray()
        self._inflator = zlib.decompressobj()

    @property
    def latency(self) -> t.Optional[float]:
        if self.keep_alive:
            return self.keep_alive.latency

    def is_closed(self) -> bool:
        return self._closed

    async def close(self, code: t.Optional[int] = None) -> None:
        if self._closed:
            return

        if code is None:
            code = 4000

        if self.keep_alive:
            self.keep_alive.stop()

        try:
            await self.socket.close(code=code)  # type: ignore
        finally:
            self.socket = None

        try:
            await self.session.close()  # type: ignore
        finally:
            self.session = None

        self.session_id = None
        self.keep_alive = None
        self.heartbeat_interval = _DEFAULT_INTERVAL
        self._seq = None
        self._closed = True
        self._buffer = bytearray()

    async def connect(self, resume: bool = False) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession()

        wss = self.gateway["url"] + '?' + urlencode(
            {'v': self._VERSION, "encoding": "json", "compress": "zlib-stream"}
        )

        self.socket = await self.session.ws_connect(wss)
        self._closed = False

        await self.poll_event()

        packet = (self.resume()
                  if resume else self.identify())

        await self.send(packet)

    async def poll_event(self) -> None:
        assert self.socket

        try:
            timeout = self.heartbeat_interval*2 + 20
            message = await self.socket.receive(timeout=timeout)
        except asyncio.TimeoutError:
            await self.close()
            raise errors.ReconnectWebSocket() from None

        type_: MType = message.type  # type: ignore

        if type_ is MType.ERROR:
            raise message.error

        if type_ in (MType.TEXT, MType.BINARY):
            if self.keep_alive:
                self.keep_alive.recv()

            payload = await self.parse_raw_message(message.data)
            if not payload:
                return

            return await self.handle_payload(payload)

        if type_ is MType.CLOSE:
            code = message.data

            if code not in (1000, 4004, 4010, 4011, 4012, 4013, 4014):
                await self.close()
                raise errors.ReconnectWebSocket()

            raise errors.GatewayConnection(code, message.extra)

        if type_ in (MType.CLOSING, MType.CLOSED):
            await self.close()
            raise errors.ReconnectWebSocket()

        await self._unknown_message(message)

    async def _unknown_message(self, message: WSMessage, /) -> None:
        pass

    async def parse_raw_message(self, data: t.Union[str, bytes]) -> t.Optional[Payload]:
        if type(data) is bytes:
            self._buffer.extend(data)

            if len(data) < 4 or data[-4:] != b'\x00\x00\xff\xff':
                return

            data = self._inflator.decompress(self._buffer)
            # data = data.decode('utf-8')

            self._buffer.clear()

        return json.loads(data)

    async def handle_payload(self, payload: Payload) -> None:
        op = int(payload["op"])
        d = payload['d']

        if op is self.HELLO:
            self.heartbeat_interval = d["heartbeat_interval"]

            interval = self.heartbeat_interval / 1000
            self.keep_alive = KeepAlive(self, interval)

            return self.keep_alive.start()

        if op is self.HEARTBEAT_ACK:
            assert self.keep_alive
            return self.keep_alive.ack()

        if op is self.INVALID_SESSION:
            if d is True:
                await self.close()
                raise errors.ReconnectWebSocket()

            await self.close(1000)
            raise errors.GatewayError("can't reconnect")

        if op is self.RECONNECT:
            await self.close(1000)
            raise errors.ReconnectWebSocket()

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

    async def _unknown_payload(self, payload: Payload, /) -> None:
        pass

    def send(self, data: t.Union[bytes, str, Packet]) -> t.Coroutine[t.Any, t.Any, None]:
        assert self.socket

        if type(data) is bytes:
            return self.socket.send_bytes(data)

        if type(data) is str:
            return self.socket.send_str(data)

        return self.socket.send_json(data)

    # Packets

    def identify(self) -> Packet:
        """Returns the `IDENTIFY` packet."""
        return {
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

    def resume(self) -> Packet:
        """Returns the `RESUME` packet."""
        return {
            "op": self.RESUME,
            'd': {
                "seq": self._seq,
                "token": self.token,
                "session_id": self.session_id,
            }
        }

    def heartbeat(self) -> Packet:
        """Returns the `HEARTBEAT` packet."""
        return {
            "op": self.HEARTBEAT,
            'd': self._seq,
        }
