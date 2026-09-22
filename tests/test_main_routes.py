import unittest

from httpx import ASGITransport, AsyncClient

from app.main import app


class MainPageRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_home_page_renders_with_the_current_template_api(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Community Network Builder", response.text)
        self.assertIn('id="root"', response.text)
        self.assertIn('id="current_user"', response.text)
        self.assertNotIn('href="/login"', response.text)


if __name__ == "__main__":
    unittest.main()
