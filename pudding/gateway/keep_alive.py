import time
import asyncio
import traceback
import threading
from typing import Coroutine, NoReturn, Any


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

    def __init__(self, ws, interval: int, *args, **kwargs) -> None:
        self.ws       = ws
        self.interval = interval

        super().__init__(daemon=True, *args, **kwargs)

        self.latency = None
        self._event = threading.Event()
        self._last_ack = time.perf_counter()
        self._last_send = time.perf_counter()
        self._last_recv = time.perf_counter()

    def run(self) -> NoReturn:
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

    def send_heartbeat_packet(self) -> Coroutine[Any, Any, None]:
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

    def send(self, _=None) -> None:
        self._last_send = time.perf_counter()
