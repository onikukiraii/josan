from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from entity.member import Member
from entity.shift_request import ShiftRequest


class TestGetShiftRequests:
    def test_get_empty(self, client: TestClient) -> None:
        resp = client.get("/shift-requests/", params={"year_month": "2025-01"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_with_data(
        self,
        client: TestClient,
        db_session: Session,
        create_member: Callable[..., Member],
    ) -> None:
        import datetime

        m = create_member(name="希望休メンバー")
        db_session.add(ShiftRequest(member_id=m.id, year_month="2025-01", date=datetime.date(2025, 1, 10)))
        db_session.commit()

        resp = client.get("/shift-requests/", params={"year_month": "2025-01"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["member_name"] == "希望休メンバー"
        assert data[0]["date"] == "2025-01-10"


class TestBulkUpdateShiftRequests:
    def test_bulk_put_creates(self, client: TestClient, create_member: Callable[..., Member]) -> None:
        m = create_member(name="希望休作成")
        resp = client.put(
            "/shift-requests/",
            json={
                "member_id": m.id,
                "year_month": "2025-01",
                "dates": ["2025-01-05", "2025-01-12", "2025-01-19"],
            },
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_bulk_put_replaces(self, client: TestClient, create_member: Callable[..., Member]) -> None:
        m = create_member(name="希望休置換")
        client.put(
            "/shift-requests/",
            json={"member_id": m.id, "year_month": "2025-01", "dates": ["2025-01-05", "2025-01-12"]},
        )
        resp = client.put(
            "/shift-requests/",
            json={"member_id": m.id, "year_month": "2025-01", "dates": ["2025-01-20"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["date"] == "2025-01-20"

    def test_bulk_put_empty_dates(self, client: TestClient, create_member: Callable[..., Member]) -> None:
        m = create_member(name="希望休全削除")
        client.put(
            "/shift-requests/",
            json={"member_id": m.id, "year_month": "2025-01", "dates": ["2025-01-05"]},
        )
        resp = client.put(
            "/shift-requests/",
            json={"member_id": m.id, "year_month": "2025-01", "dates": []},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_bulk_put_member_not_found(self, client: TestClient) -> None:
        resp = client.put(
            "/shift-requests/",
            json={"member_id": 9999, "year_month": "2025-01", "dates": ["2025-01-05"]},
        )
        assert resp.status_code == 404
