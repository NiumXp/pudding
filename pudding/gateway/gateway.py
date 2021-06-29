from typing import Optional
from urllib.parse import urlencode
from dataclasses import dataclass, field

DEFAULT_ENCODING = "json"
DEFAULT_COMPRESS = "zlib-stream"


@dataclass
class Gateway:
    url: str
    version: Optional[int] = field(default=None)
    compress: Optional[str] = field(default=DEFAULT_COMPRESS)
    encoding: Optional[str] = field(default=DEFAULT_ENCODING)

    @property
    def wss(self) -> str:
        url = self.url

        query = {}
        if self.version:  query['v']        = self.version
        if self.compress: query["compress"] = self.compress
        if self.encoding: query["encoding"] = self.encoding

        if query:
            url += '?' + urlencode(query)

        return url
