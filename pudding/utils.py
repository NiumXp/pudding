import typing as t


class suppress_all:
    __slots__ = "exc"

    def __init__(self, exc: t.Type[BaseException] = Exception) -> None:
        self.exc = exc

    def __enter__(self) -> None:
        return

    def __exit__(self, t: t.Type[BaseException], *_: t.Any) -> bool:
        if not t:
            return False

        return issubclass(t, self.exc)
