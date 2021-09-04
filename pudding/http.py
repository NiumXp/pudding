import json
import typing as t

from aiohttp import ClientSession

from . import errors, utils, types
from .types import GatewayPayload, GatewayBotPayload


class Route:
    __slots__ = ("_method", "_path", "auth")

    BASE: t.ClassVar[str] = "https://discord.com/api/v9"

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
        "_user_agent",
    )

    def __init__(self, token: t.Optional[str] = None) -> None:
        self.token = token

        self.session: t.Optional[ClientSession] = None
        self._closed = False
        self._user_agent = "DiscordBot"

    def is_closed(self) -> bool:
        return self._closed

    async def close(self) -> None:
        if self._closed:
            return

        with utils.suppress_all():
            await self.session.close()  # type: ignore

        self.session = None
        self._closed = True

    async def request(self, route: Route, *, reason: t.Optional[str] = None) -> t.Any:
        if self._closed:
            return

        if not self.session:
            self.session = ClientSession()

        headers: t.Dict[str, str] = {
            "User-Agent": self._user_agent,
        }

        if reason:
            headers["X-Audit-Log-Reason"] = reason

        if route.auth and self.token:
            headers["Authorization"] = "Bot " + self.token

        async with self.session.request(route.method, route.url, headers=headers) as response:
            data = await response.text()

            if response.headers.get("Content-Type") == "application/json":
                data = json.loads(data)

            if 300 > response.status >= 200:
                return data

            raise errors.HTTPException()

    async def get_gateway(self) -> GatewayPayload:
        r = Route("GET", "/gateway", auth=False)
        return await self.request(r)

    async def get_bot_gateway(self) -> GatewayBotPayload:
        r = Route("GET", "/gateway/bot")
        return await self.request(r)

    async def get_channel(self, id: int) -> types.Channel:
        r = Route("GET", "/channels/{id}", id=id)
        return await self.request(r)

    async def delete_channel(self, id: int, *, reason: t.Optional[str] = None) -> None:
        r = Route("DELETE", "/channels/{id}", id=id)
        return await self.request(r, reason=reason)

