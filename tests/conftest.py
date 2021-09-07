import os
from typing import Optional

import pytest
import dotenv

import pudding

dotenv.load_dotenv(override=True)  # type: ignore


@pytest.fixture
async def http():
    token: Optional[str] = os.getenv("TEST_TOKEN")
    assert token, "The 'TEST_TOKEN' env var is not defined"

    client = pudding.DiscordHTTPClient(token)
    yield client

    await client.close()
