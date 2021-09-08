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

    async def request(
        self,
        route: Route,
        *,
        reason: t.Optional[str] = None,
        **kwargs: t.Any,
    ) -> t.Any:
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

        kwargs["url"] = route.url
        kwargs["method"] = route.method
        kwargs["headers"] = headers

        async with self.session.request(**kwargs) as response:
            data = await response.text()

            if response.headers.get("Content-Type") == "application/json":
                data = json.loads(data)

            if 300 > response.status >= 200:
                return data

            if response.status == 404:
                raise errors.NotFound()

            raise errors.HTTPException()

    # Audit Log

    # Channel

    async def get_channel(self, id: types.Snowflake) -> types.Channel:
        r = Route("GET", "/channels/{id}", id=id)
        return await self.request(r)

    async def delete_channel(
        self,
        id: types.Snowflake,
        *,
        reason: t.Optional[str] = None,
    ) -> None:
        r = Route("DELETE", "/channels/{id}", id=id)
        return await self.request(r, reason=reason)

    # Emoji

    async def get_guild_emojis(
        self,
        guild_id: types.Snowflake,
    ) -> t.List[types.Emoji]:
        r = Route(
            "GET", "/guilds/{guild_id}/emojis",

            guild_id=guild_id
        )

        return await self.request(r)

    async def get_guild_emoji(
        self,
        guild_id: types.Snowflake,
        emoji_id: types.Snowflake,
    ) -> types.Emoji:
        r = Route(
            "GET", "/guilds/{guild_id}/emojis/{emoji_id}",

            guild_id=guild_id,
            emoji_id=emoji_id,
        )

        return await self.request(r)

    async def create_guild_emoji(
        self,
        guild_id: types.Snowflake,
        *,
        name: str,
        image: bytes,
        roles: t.Optional[t.List[types.Snowflake]] = None,
        reason: t.Optional[str] = None,
    ) -> types.Emoji:
        ...

    async def edit_guild_emoji(
        self,
        guild_id: types.Snowflake,
        emoji_id: types.Snowflake,
        *,
        name: t.Optional[str] = None,
        roles: t.Optional[t.List[types.Snowflake]] = None,
        reason: t.Optional[str] = None,
    ) -> types.Emoji:
        ...

    async def delete_guild_emoji(
        self,
        guild_id: types.Snowflake,
        emoji_id: types.Snowflake,
        *,
        reason: t.Optional[str] = None,
    ) -> types.Emoji:
        r = Route(
            "DELETE", "/guilds/{guild_id}/emojis/{emoji_id}",

            guild_id=guild_id,
            emoji_id=emoji_id,
        )

        return await self.request(r, reason=reason)

    # Guild

    async def get_guild(
        self,
        guild_id: types.Snowflake
    ) -> types.Guild:
        r = Route("GET", "/guilds/{guild_id}", guild_id=guild_id)

        return await self.request(r)

    # Guild Template

    # Invite

    async def get_invite(
        self,
        invite_code: str,
        *,
        with_counts: t.Optional[bool] = None,
        with_expiration: t.Optional[bool] = None,
    ) -> types.Invite:
        params = {}

        if with_counts is not None:
            params["with_counts"] = with_counts

        if with_expiration is not None:
            params["with_expiration"] = with_expiration

        r = Route("GET", "/invites/{invite_code}", invite_code=invite_code,)
        return await self.request(r, params=params)

    async def delete_invite(
        self,
        invite_code: str,
        *,
        reason: t.Optional[str] = None,
    ) -> None:
        r = Route("DELETE", "/invites/{invite_code}", invite_code=invite_code,)
        return await self.request(r, reason=reason)

    # Stage instance

    # Sticker

    # User

    async def get_user(self, id: types.Snowflake) -> types.User:
        r = Route("GET", "/users/{id}", id=id)
        return await self.request(r)

    async def get_current_user(self) -> types.User:
        return await self.get_user("@me")

    # Voice

    # Webhook

    # Gateway

    async def get_gateway(self) -> GatewayPayload:
        r = Route("GET", "/gateway", auth=False)
        return await self.request(r)

    async def get_bot_gateway(self) -> GatewayBotPayload:
        r = Route("GET", "/gateway/bot")
        return await self.request(r)
