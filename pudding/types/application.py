import typing as t
from .snowflake import Snowflake


class PartialApplication:
    pass


class Application(t.TypedDict):
    id: Snowflake
    name: str
    icon: t.Optional[str]
    description: str
