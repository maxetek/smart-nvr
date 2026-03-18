
from httpx import AsyncClient


class TestRBAC:
    async def test_viewer_cannot_create_camera(
        self, client: AsyncClient, viewer_headers
    ):
        resp = await client.post(
            "/api/v1/cameras/",
            json={"name": "Cam", "rtsp_url": "rtsp://test:554/s"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    async def test_operator_can_create_camera(
        self, client: AsyncClient, operator_headers
    ):
        resp = await client.post(
            "/api/v1/cameras/",
            json={
                "name": "Operator Cam",
                "rtsp_url": "rtsp://test:554/stream",
            },
            headers=operator_headers,
        )
        assert resp.status_code == 201

    async def test_admin_can_list_users(self, client: AsyncClient, admin_headers):
        resp = await client.get("/api/v1/users/", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    async def test_operator_cannot_list_users(
        self, client: AsyncClient, operator_headers
    ):
        resp = await client.get("/api/v1/users/", headers=operator_headers)
        assert resp.status_code == 403

    async def test_viewer_cannot_list_users(self, client: AsyncClient, viewer_headers):
        resp = await client.get("/api/v1/users/", headers=viewer_headers)
        assert resp.status_code == 403

    async def test_admin_can_change_role(
        self, client: AsyncClient, admin_headers, viewer_user
    ):
        resp = await client.put(
            f"/api/v1/users/{viewer_user.id}/role",
            json={"role": "operator"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "operator"

    async def test_operator_cannot_change_role(
        self, client: AsyncClient, operator_headers, viewer_user
    ):
        resp = await client.put(
            f"/api/v1/users/{viewer_user.id}/role",
            json={"role": "admin"},
            headers=operator_headers,
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_delete_camera(
        self, client: AsyncClient, viewer_headers, sample_camera
    ):
        resp = await client.delete(
            f"/api/v1/cameras/{sample_camera.id}", headers=viewer_headers
        )
        assert resp.status_code == 403

    async def test_operator_cannot_delete_camera(
        self, client: AsyncClient, operator_headers, sample_camera
    ):
        resp = await client.delete(
            f"/api/v1/cameras/{sample_camera.id}", headers=operator_headers
        )
        assert resp.status_code == 403

    async def test_get_me(self, client: AsyncClient, admin_headers, admin_user):
        resp = await client.get("/api/v1/users/me", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testadmin"
        assert data["role"] == "admin"

    async def test_admin_cannot_deactivate_self(
        self, client: AsyncClient, admin_headers, admin_user
    ):
        resp = await client.delete(
            f"/api/v1/users/{admin_user.id}", headers=admin_headers
        )
        assert resp.status_code == 400
