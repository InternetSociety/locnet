import unittest
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.config import settings
from app.security import minimum_authentication_response_time


class AuthenticationResponseTimingTests(unittest.IsolatedAsyncioTestCase):
    async def test_waits_until_the_minimum_response_time(self):
        with (
            patch(
                "app.security.AUTHENTICATION_MINIMUM_RESPONSE_SECONDS",
                1.0,
            ),
            patch("app.security.monotonic", side_effect=(10.0, 10.25)),
            patch("app.security.asyncio.sleep", new_callable=AsyncMock) as sleep,
        ):
            async with minimum_authentication_response_time():
                pass

        sleep.assert_awaited_once_with(0.75)


async def test_authentication_forms_apply_the_minimum_response_time(
    client: AsyncClient,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.security.AUTHENTICATION_MINIMUM_RESPONSE_SECONDS",
        1.0,
    )
    submissions = (
        (
            "/login",
            {
                "email": "unknown@example.com",
                "password": "not the password",
            },
        ),
        ("/forgot-password", {"email": "unknown@example.com"}),
        (
            "/reset-password",
            {
                "code": "not a valid code",
                "password": "a valid new password",
            },
        ),
    )

    for path, data in submissions:
        page = await client.get(path)
        data["csrf_token"] = page.cookies[settings.csrf_cookie_name]
        with (
            patch("app.security.monotonic", side_effect=(10.0, 10.25)),
            patch("app.security.asyncio.sleep", new_callable=AsyncMock) as sleep,
        ):
            await client.post(path, data=data)

        sleep.assert_awaited_once_with(0.75)


if __name__ == "__main__":
    unittest.main()
