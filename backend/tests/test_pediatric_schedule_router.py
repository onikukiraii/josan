from fastapi.testclient import TestClient


class TestGetPediatricSchedules:
    def test_get_empty(self, client: TestClient) -> None:
        resp = client.get("/pediatric-doctor-schedules/", params={"year_month": "2025-01"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_filters_by_month(self, client: TestClient) -> None:
        client.put(
            "/pediatric-doctor-schedules/",
            json={"year_month": "2025-01", "dates": ["2025-01-10", "2025-01-20"]},
        )
        client.put(
            "/pediatric-doctor-schedules/",
            json={"year_month": "2025-02", "dates": ["2025-02-05"]},
        )
        resp = client.get("/pediatric-doctor-schedules/", params={"year_month": "2025-01"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(d["date"].startswith("2025-01") for d in data)


class TestBulkUpdatePediatricSchedules:
    def test_bulk_put_creates(self, client: TestClient) -> None:
        resp = client.put(
            "/pediatric-doctor-schedules/",
            json={"year_month": "2025-01", "dates": ["2025-01-08", "2025-01-15", "2025-01-22"]},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_bulk_put_replaces(self, client: TestClient) -> None:
        client.put(
            "/pediatric-doctor-schedules/",
            json={"year_month": "2025-01", "dates": ["2025-01-08", "2025-01-15"]},
        )
        resp = client.put(
            "/pediatric-doctor-schedules/",
            json={"year_month": "2025-01", "dates": ["2025-01-22"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["date"] == "2025-01-22"

    def test_bulk_put_empty(self, client: TestClient) -> None:
        client.put(
            "/pediatric-doctor-schedules/",
            json={"year_month": "2025-01", "dates": ["2025-01-08"]},
        )
        resp = client.put(
            "/pediatric-doctor-schedules/",
            json={"year_month": "2025-01", "dates": []},
        )
        assert resp.status_code == 200
        assert resp.json() == []
