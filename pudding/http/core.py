import typing as t

from aiohttp import ClientSession

from ..gateway import GatewayPayload, GatewayBotPayload


class Route:
    __slots__ = ("_method", "_path", "auth")

    BASE = "https://discord.com/api/v9"

    def __init__(self, method: str, path: str, *, auth: bool = True, **params: t.Any) -> None:
        path = path.format_map(params)

        self._method = method
        self._path = path
        self.auth = auth

    def __repr__(self) -> str:
        return "Route({0.method!r}, {0.path!r}, auth={0.auth})".format(self)

    @property
    def method(self) -> str:
        return self._method.upper()

    @property
    def path(self) -> str:
        return '/' + self._path.lstrip('/')

    @property
    def url(self) -> str:
        return self.BASE + self.path


class DiscordHTTPClient:
    __slots__ = (
        "token",

        "session",
        "_closed",
    )

    def __init__(self, token: t.Optional[str]) -> None:
        self.token = token

        self.session: t.Optional[ClientSession] = None
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

    async def request(self, route: Route) -> t.Any:
        pass

    async def get_gateway(self) -> GatewayBotPayload:
        return {"url": "wss://gateway.discord.gg/"}  # :D

    async def get_bot_gateway(self) -> GatewayPayload:
        return await self.get_gateway()  # :D
