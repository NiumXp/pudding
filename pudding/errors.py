class PuddingError(Exception):
    pass


class HTTPException(PuddingError):
    pass


class NotFound(HTTPException):
    pass


class GatewayError(PuddingError):
    pass


class ReconnectWebSocket(GatewayError):
    pass


class GatewayConnection(GatewayError):
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message

        super().__init__(f"Gateway closed {code}: {message}")
