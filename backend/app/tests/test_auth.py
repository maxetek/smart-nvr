from httpx import AsyncClient

from app.auth.jwt import create_access_token, create_refresh_token


class TestLogin:
    async def test_login_success(self, client: AsyncClient, admin_user):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "testadmin", "password": "AdminPass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, admin_user):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "testadmin", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "nothing"},
        )
        assert resp.status_code == 401


class TestRegister:
    async def test_register_first_user_becomes_admin(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "firstuser",
                "email": "first@test.com",
                "password": "StrongPass123",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data

    async def test_register_requires_auth_when_users_exist(
        self, client: AsyncClient, admin_user
    ):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "StrongPass123",
            },
        )
        assert resp.status_code == 401

    async def test_register_as_admin(self, client: AsyncClient, admin_user, admin_headers):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "StrongPass123",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201


class TestRefresh:
    async def test_refresh_token(self, client: AsyncClient, admin_user):
        refresh = create_refresh_token({"sub": str(admin_user.id), "role": admin_user.role})
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    async def test_refresh_with_access_token_fails(self, client: AsyncClient, admin_user):
        access = create_access_token({"sub": str(admin_user.id), "role": admin_user.role})
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access},
        )
        assert resp.status_code == 401


class TestProtectedEndpoint:
    async def test_no_token_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/cameras/")
        assert resp.status_code == 401

    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/cameras/",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert resp.status_code == 401

    async def test_valid_token_works(self, client: AsyncClient, admin_user, admin_headers):
        resp = await client.get("/api/v1/cameras/", headers=admin_headers)
        assert resp.status_code == 200
