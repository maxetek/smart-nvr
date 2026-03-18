import uuid

from httpx import AsyncClient


class TestPatternCRUD:
    async def test_create_pattern(
        self, client: AsyncClient, admin_headers, sample_camera
    ):
        resp = await client.post(
            "/api/v1/patterns/",
            json={
                "camera_id": str(sample_camera.id),
                "name": "Entry Zone",
                "pattern_type": "zone_intrusion",
                "config_json": {
                    "zone": [[0, 0], [100, 0], [100, 100], [0, 100]],
                    "threshold": 0.5,
                },
                "cooldown_seconds": 30,
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Entry Zone"
        assert data["pattern_type"] == "zone_intrusion"
        assert data["cooldown_seconds"] == 30

    async def test_list_patterns(
        self, client: AsyncClient, admin_headers, sample_camera
    ):
        # Create a pattern first
        await client.post(
            "/api/v1/patterns/",
            json={
                "camera_id": str(sample_camera.id),
                "name": "Test Pattern",
                "pattern_type": "line_cross",
                "config_json": {"line": [[0, 50], [100, 50]]},
            },
            headers=admin_headers,
        )
        resp = await client.get("/api/v1/patterns/", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_list_patterns_by_camera(
        self, client: AsyncClient, admin_headers, sample_camera
    ):
        await client.post(
            "/api/v1/patterns/",
            json={
                "camera_id": str(sample_camera.id),
                "name": "Cam Pattern",
                "pattern_type": "loitering",
                "config_json": {"zone": [[0, 0], [50, 50]]},
            },
            headers=admin_headers,
        )
        resp = await client.get(
            "/api/v1/patterns/",
            params={"camera_id": str(sample_camera.id)},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_get_pattern_detail(
        self, client: AsyncClient, admin_headers, sample_camera
    ):
        create_resp = await client.post(
            "/api/v1/patterns/",
            json={
                "camera_id": str(sample_camera.id),
                "name": "Detail Pattern",
                "pattern_type": "smoking",
                "config_json": {"confidence": 0.7},
            },
            headers=admin_headers,
        )
        pattern_id = create_resp.json()["id"]
        resp = await client.get(
            f"/api/v1/patterns/{pattern_id}", headers=admin_headers
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Detail Pattern"

    async def test_update_pattern(
        self, client: AsyncClient, admin_headers, sample_camera
    ):
        create_resp = await client.post(
            "/api/v1/patterns/",
            json={
                "camera_id": str(sample_camera.id),
                "name": "To Update",
                "pattern_type": "crowd",
                "config_json": {"max_people": 10},
            },
            headers=admin_headers,
        )
        pattern_id = create_resp.json()["id"]
        resp = await client.put(
            f"/api/v1/patterns/{pattern_id}",
            json={"name": "Updated Pattern", "cooldown_seconds": 120},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Pattern"
        assert resp.json()["cooldown_seconds"] == 120

    async def test_delete_pattern_admin(
        self, client: AsyncClient, admin_headers, sample_camera
    ):
        create_resp = await client.post(
            "/api/v1/patterns/",
            json={
                "camera_id": str(sample_camera.id),
                "name": "To Delete",
                "pattern_type": "weapon",
                "config_json": {"confidence": 0.9},
            },
            headers=admin_headers,
        )
        pattern_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/patterns/{pattern_id}", headers=admin_headers
        )
        assert resp.status_code == 204

    async def test_viewer_cannot_create_pattern(
        self, client: AsyncClient, viewer_headers, sample_camera
    ):
        resp = await client.post(
            "/api/v1/patterns/",
            json={
                "camera_id": str(sample_camera.id),
                "name": "Blocked",
                "pattern_type": "line_cross",
                "config_json": {},
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    async def test_delete_pattern_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.delete(
            f"/api/v1/patterns/{uuid.uuid4()}", headers=admin_headers
        )
        assert resp.status_code == 404
