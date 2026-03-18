import uuid

from httpx import AsyncClient


class TestEventAPI:
    async def test_list_events(
        self, client: AsyncClient, admin_headers, sample_event
    ):
        resp = await client.get("/api/v1/events/", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_list_events_with_filters(
        self, client: AsyncClient, admin_headers, sample_event
    ):
        resp = await client.get(
            "/api/v1/events/",
            params={"event_type": "line_cross", "severity": "warning"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_list_events_filter_no_match(
        self, client: AsyncClient, admin_headers, sample_event
    ):
        resp = await client.get(
            "/api/v1/events/",
            params={"event_type": "nonexistent_type"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    async def test_get_event_detail(
        self, client: AsyncClient, admin_headers, sample_event
    ):
        resp = await client.get(
            f"/api/v1/events/{sample_event.id}", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_type"] == "line_cross"
        assert data["severity"] == "warning"

    async def test_get_event_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.get(
            f"/api/v1/events/{uuid.uuid4()}", headers=admin_headers
        )
        assert resp.status_code == 404

    async def test_acknowledge_events(
        self, client: AsyncClient, admin_headers, sample_event
    ):
        resp = await client.post(
            "/api/v1/events/acknowledge",
            json={"event_ids": [str(sample_event.id)]},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["acknowledged"] == 1

    async def test_acknowledge_requires_operator_or_admin(
        self, client: AsyncClient, viewer_headers, sample_event
    ):
        resp = await client.post(
            "/api/v1/events/acknowledge",
            json={"event_ids": [str(sample_event.id)]},
            headers=viewer_headers,
        )
        assert resp.status_code == 403
