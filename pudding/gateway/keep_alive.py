import time
import asyncio
import traceback
import threading
from typing import NoReturn


class KeepAlive(threading.Thread):
    __slots__ = (
        "ws",
        "interval",
        "latency",
        "_event",
        "_last_send",
        "_last_recv",
    )

    def __init__(self, ws, interval: int, *args, **kwargs) -> None:
        self.ws       = ws
        self.interval = interval

        super().__init__(daemon=True, *args, **kwargs)

        self.latency = None
        self._event = threading.Event()
        self._last_send = time.perf_counter()
        self._last_recv = time.perf_counter()

    def run(self) -> NoReturn:
        while not self._event.wait(self.interval):
            if self._last_recv + 15 < time.perf_counter():
                coro = self.ws.close(4000)

                future = asyncio.run_coroutine_threadsafe(coro, self.ws.loop)

                try:
                    future.result()
                finally:
                    return self.stop()

            coro = self.ws.heartbeat()
            future = asyncio.run_coroutine_threadsafe(coro, self.ws.loop)

            try:
                future.result()
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                return self.stop()

            self._last_send = time.perf_counter()

    def stop(self) -> None:
        if not self._event.is_set():
            self._event.set()

    def ack(self) -> None:
        now = time.perf_counter()
        self.latency = now - self._last_send

    def recv(self) -> None:
        self._last_recv = time.perf_counter()
