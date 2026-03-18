import uuid

from httpx import AsyncClient


class TestCameraCRUD:
    async def test_create_camera_as_admin(self, client: AsyncClient, admin_headers):
        resp = await client.post(
            "/api/v1/cameras/",
            json={
                "name": "Front Door Camera",
                "rtsp_url": "rtsp://192.168.1.10:554/stream1",
                "location": "Front Door",
                "width": 1920,
                "height": 1080,
                "fps": 30,
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Front Door Camera"
        assert data["location"] == "Front Door"
        # RTSP URL must NOT be exposed
        assert "rtsp_url" not in data
        assert "rtsp_url_encrypted" not in data

    async def test_create_camera_as_viewer_forbidden(
        self, client: AsyncClient, viewer_headers
    ):
        resp = await client.post(
            "/api/v1/cameras/",
            json={
                "name": "Test Cam",
                "rtsp_url": "rtsp://test:554/stream",
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    async def test_list_cameras_paginated(
        self, client: AsyncClient, admin_headers, sample_camera
    ):
        resp = await client.get(
            "/api/v1/cameras/", params={"limit": 10, "offset": 0}, headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "has_more" in data
        assert data["total"] >= 1

    async def test_get_camera_detail(
        self, client: AsyncClient, admin_headers, sample_camera
    ):
        resp = await client.get(
            f"/api/v1/cameras/{sample_camera.id}", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Camera 1"
        assert "rtsp_url" not in data

    async def test_update_camera(self, client: AsyncClient, admin_headers, sample_camera):
        resp = await client.put(
            f"/api/v1/cameras/{sample_camera.id}",
            json={"name": "Updated Camera", "location": "Back Door"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Camera"
        assert data["location"] == "Back Door"

    async def test_delete_camera_as_admin(
        self, client: AsyncClient, admin_headers, sample_camera
    ):
        resp = await client.delete(
            f"/api/v1/cameras/{sample_camera.id}", headers=admin_headers
        )
        assert resp.status_code == 204

    async def test_delete_camera_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.delete(
            f"/api/v1/cameras/{uuid.uuid4()}", headers=admin_headers
        )
        assert resp.status_code == 404

    async def test_get_camera_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.get(
            f"/api/v1/cameras/{uuid.uuid4()}", headers=admin_headers
        )
        assert resp.status_code == 404
