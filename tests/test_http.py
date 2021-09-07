import pytest
import pudding

DEFAULT_USER_ID = 256444020413300736
DEFAULT_USER_NAME = "Nium"


pytestmark = pytest.mark.asyncio


async def test_get_user(http: pudding.DiscordHTTPClient):
    user = await http.get_user(DEFAULT_USER_ID)

    assert user["id"] == str(DEFAULT_USER_ID)
    assert user["username"] == DEFAULT_USER_NAME


async def test_user_not_found(http: pudding.DiscordHTTPClient):
    with pytest.raises(pudding.errors.NotFound):
        await http.get_user(0)
