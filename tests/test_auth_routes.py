from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.repositories import UserRepository
from app.services.users import UserService


async def create_user(
    session: AsyncSession,
    email: str = "person@example.com",
    *,
    is_admin: bool = False,
):
    return await UserService(UserRepository(session)).create_user(
        email,
        "correct horse battery staple",
        is_admin=is_admin,
    )


async def sign_in(client: AsyncClient, email: str = "person@example.com"):
    page = await client.get("/login")
    csrf_token = page.cookies[settings.csrf_cookie_name]
    return await client.post(
        "/login",
        data={
            "email": email,
            "password": "correct horse battery staple",
            "csrf_token": csrf_token,
        },
    )


async def test_public_home_page_is_the_application_and_does_not_advertise_login(
    client: AsyncClient,
):
    response = await client.get("/")

    assert response.status_code == 200
    assert "Community Network Builder" in response.text
    assert 'id="root"' in response.text
    assert 'id="current_user"' in response.text
    assert 'class="sign-in-panel"' not in response.text
    assert 'href="/login"' not in response.text


async def test_login_page_is_available_only_at_the_unlinked_route(client: AsyncClient):
    response = await client.get("/login")

    assert response.status_code == 200
    assert 'class="sign-in-panel"' in response.text
    assert 'action="/login"' in response.text
    assert '<meta name="robots" content="noindex, nofollow">' in response.text


async def test_robots_txt_discourages_indexing_authentication_routes(client: AsyncClient):
    response = await client.get("/robots.txt")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "Disallow: /login" in response.text
    assert "Disallow: /docs" in response.text


async def test_public_resources_are_available_without_a_session(client: AsyncClient):
    for path in ("/qsg", "/documentation", "/faq"):
        response = await client.get(path)

        assert response.status_code == 200
        assert 'href="/"' in response.text


async def test_landing_language_selection_is_preserved(client: AsyncClient):
    response = await client.get("/login?lang=es")

    assert response.status_code == 200
    assert '<option value="es" selected>Español</option>' in response.text
    assert 'href="/qsg?lang=es"' in response.text
    assert 'name="lang" value="es"' in response.text


async def test_sign_in_sets_http_only_session_and_opens_the_spa(
    client: AsyncClient,
    database_session: AsyncSession,
):
    await create_user(database_session)

    response = await sign_in(client)

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    session_cookie = response.cookies[settings.session_cookie_name]
    assert session_cookie
    assert "httponly" in response.headers["set-cookie"].lower()
    spa = await client.get("/")
    assert spa.status_code == 200
    assert "Community Network Builder" in spa.text


async def test_invalid_sign_in_is_safe(
    client: AsyncClient,
    database_session: AsyncSession,
):
    await create_user(database_session)
    page = await client.get("/login")
    csrf_token = page.cookies[settings.csrf_cookie_name]

    response = await client.post(
        "/login",
        data={
            "email": "person@example.com",
            "password": "incorrect password",
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 400
    assert "Invalid email, password, or account status" in response.text
    assert settings.session_cookie_name not in response.cookies


async def test_api_requires_an_enabled_persistent_token(
    client: AsyncClient,
    database_session: AsyncSession,
):
    user = await create_user(database_session)
    anonymous = await client.get("/api/defaults")
    assert anonymous.status_code == 401
    assert anonymous.headers["www-authenticate"] == "Bearer"

    await sign_in(client)
    session_response = await client.get("/api/defaults")
    assert session_response.status_code == 401

    service = UserService(UserRepository(database_session))
    issued = await service.enable_api_access(user.id)
    client.cookies.clear()
    token_response = await client.get(
        "/api/defaults",
        headers={"Authorization": f"Bearer {issued.token}"},
    )
    assert token_response.status_code == 200


async def test_public_browser_service_posts_require_csrf(
    client: AsyncClient,
    database_session: AsyncSession,
):
    await create_user(database_session)
    page = await client.get("/")

    rejected = await client.post("/web/api/characteristics", json={"iso_3": "NZL"})
    assert rejected.status_code == 403
    forged_bearer = await client.post(
        "/web/api/characteristics",
        json={"iso_3": "NZL"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert forged_bearer.status_code == 403

    accepted = await client.post(
        "/web/api/characteristics",
        json={"iso_3": "NZL"},
        headers={
            "X-CSRF-Token": page.cookies[settings.csrf_cookie_name],
        },
    )
    assert accepted.status_code == 200
    external_api = await client.post(
        "/api/characteristics",
        json={"iso_3": "NZL"},
        headers={"X-CSRF-Token": page.cookies[settings.csrf_cookie_name]},
    )
    assert external_api.status_code == 401


async def test_swagger_accepts_normal_and_administrator_sessions(
    client: AsyncClient,
    database_session: AsyncSession,
):
    await create_user(database_session)
    anonymous = await client.get("/docs")
    assert anonymous.status_code == 303
    assert anonymous.headers["location"] == "/login"

    await sign_in(client)

    assert (await client.get("/docs")).status_code == 200
    openapi = await client.get("/openapi.json")
    assert openapi.status_code == 200
    assert "HTTPBearer" in openapi.json()["components"]["securitySchemes"]

    client.cookies.clear()
    await create_user(database_session, email="admin@example.com", is_admin=True)
    await sign_in(client, "admin@example.com")
    assert (await client.get("/docs")).status_code == 200
    assert (await client.get("/openapi.json")).status_code == 200


async def test_logout_requires_csrf_and_deletes_the_session(
    client: AsyncClient,
    database_session: AsyncSession,
):
    await create_user(database_session)
    await sign_in(client)

    assert (await client.post("/logout", data={"csrf_token": "wrong"})).status_code == 403
    response = await client.post(
        "/logout",
        data={"csrf_token": client.cookies[settings.csrf_cookie_name]},
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    legacy_app = await client.get("/app")
    assert legacy_app.status_code == 303
    assert legacy_app.headers["location"] == "/"
    assert (await client.get("/")).status_code == 200
