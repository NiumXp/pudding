class DiscordHTTPClient:
    __slots__ = ("token", "session",)

    def __init__(self, token: str) -> None:
        self.token = token

        self.session = None

    async def request(self, method: str, endpoint: str, **parameters):
        pass
