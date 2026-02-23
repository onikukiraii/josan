import datetime
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from entity.enums import ShiftType
from entity.member import Member
from entity.shift_request import ShiftRequest


class TestGetSchedule:
    def test_get_schedule_none(self, client: TestClient) -> None:
        resp = client.get("/schedules/", params={"year_month": "2025-01"})
        assert resp.status_code == 200
        assert resp.json() is None

    def test_get_schedule_with_assignments(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        m = create_member(name="テスト看護師")
        create_schedule(
            year_month="2025-01",
            assignments=[
                {"member_id": m.id, "date": datetime.date(2025, 1, 6), "shift_type": ShiftType.ward},
                {"member_id": m.id, "date": datetime.date(2025, 1, 7), "shift_type": ShiftType.day_off},
            ],
        )
        resp = client.get("/schedules/", params={"year_month": "2025-01"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["year_month"] == "2025-01"
        assert len(data["assignments"]) == 2


class TestUpdateAssignment:
    def test_update_assignment(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        m = create_member(name="更新テスト")
        sched = create_schedule(
            year_month="2025-01",
            assignments=[
                {"member_id": m.id, "date": datetime.date(2025, 1, 6), "shift_type": ShiftType.ward},
            ],
        )
        assignment_id = sched.assignments[0].id
        resp = client.put(
            f"/schedules/{sched.id}/assignments/{assignment_id}",
            json={"shift_type": "night", "member_id": m.id},
        )
        assert resp.status_code == 200
        assert resp.json()["shift_type"] == "night"

    def test_update_assignment_not_found(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        m = create_member(name="存在しない割当")
        sched = create_schedule(year_month="2025-01")
        resp = client.put(
            f"/schedules/{sched.id}/assignments/9999",
            json={"shift_type": "ward", "member_id": m.id},
        )
        assert resp.status_code == 404

    def test_update_assignment_member_not_found(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        m = create_member(name="メンバーなし")
        sched = create_schedule(
            year_month="2025-01",
            assignments=[
                {"member_id": m.id, "date": datetime.date(2025, 1, 6), "shift_type": ShiftType.ward},
            ],
        )
        assignment_id = sched.assignments[0].id
        resp = client.put(
            f"/schedules/{sched.id}/assignments/{assignment_id}",
            json={"shift_type": "ward", "member_id": 9999},
        )
        assert resp.status_code == 404


class TestCreateAssignment:
    def test_create_assignment(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        m = create_member(name="新規割当テスト")
        sched = create_schedule(year_month="2025-01")
        resp = client.post(
            f"/schedules/{sched.id}/assignments",
            json={"date": "2025-01-06", "shift_type": "ward", "member_id": m.id},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["member_id"] == m.id
        assert data["shift_type"] == "ward"
        assert data["date"] == "2025-01-06"

    def test_create_assignment_duplicate_shift_type_same_date_rejected(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        """同じ日・同じシフト種別に2人目を追加しようとしたら 409 で弾かれること."""
        m1 = create_member(name="重複テスト1")
        m2 = create_member(name="重複テスト2")
        sched = create_schedule(
            year_month="2025-01",
            assignments=[
                {"member_id": m1.id, "date": datetime.date(2025, 1, 15), "shift_type": ShiftType.ward},
            ],
        )
        # 同じ日・同じシフト種別に別メンバーを追加 → 拒否されるべき
        resp = client.post(
            f"/schedules/{sched.id}/assignments",
            json={"date": "2025-01-15", "shift_type": "ward", "member_id": m2.id},
        )
        assert resp.status_code == 409

    def test_create_assignment_different_date_ok(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        """同じシフト種別でも日付が違えば追加可能."""
        m1 = create_member(name="別日テスト1")
        m2 = create_member(name="別日テスト2")
        sched = create_schedule(
            year_month="2025-01",
            assignments=[
                {"member_id": m1.id, "date": datetime.date(2025, 1, 15), "shift_type": ShiftType.ward},
            ],
        )
        resp = client.post(
            f"/schedules/{sched.id}/assignments",
            json={"date": "2025-01-16", "shift_type": "ward", "member_id": m2.id},
        )
        assert resp.status_code == 201

    def test_create_assignment_different_shift_type_ok(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        """同じ日でもシフト種別が違えば追加可能."""
        m1 = create_member(name="別種別テスト1")
        m2 = create_member(name="別種別テスト2")
        sched = create_schedule(
            year_month="2025-01",
            assignments=[
                {"member_id": m1.id, "date": datetime.date(2025, 1, 15), "shift_type": ShiftType.ward},
            ],
        )
        resp = client.post(
            f"/schedules/{sched.id}/assignments",
            json={"date": "2025-01-15", "shift_type": "night", "member_id": m2.id},
        )
        assert resp.status_code == 201

    def test_create_assignment_replaces_day_off(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        """公休日にシフトを割り当てると day_off が自動削除され新シフトが作成される."""
        m = create_member(name="公休置換テスト")
        sched = create_schedule(
            year_month="2025-01",
            assignments=[
                {"member_id": m.id, "date": datetime.date(2025, 1, 10), "shift_type": ShiftType.day_off},
            ],
        )
        # day_off がある日にシフトを割り当て
        resp = client.post(
            f"/schedules/{sched.id}/assignments",
            json={"date": "2025-01-10", "shift_type": "ward", "member_id": m.id},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["shift_type"] == "ward"
        assert data["member_id"] == m.id

        # スケジュール全体を取得して day_off が消えていることを確認
        detail = client.get("/schedules/", params={"year_month": "2025-01"}).json()
        assignments_on_day = [a for a in detail["assignments"] if a["date"] == "2025-01-10" and a["member_id"] == m.id]
        assert len(assignments_on_day) == 1
        assert assignments_on_day[0]["shift_type"] == "ward"


class TestDeleteAssignment:
    def test_delete_assignment(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        m = create_member(name="削除テスト")
        sched = create_schedule(
            year_month="2025-01",
            assignments=[
                {"member_id": m.id, "date": datetime.date(2025, 1, 6), "shift_type": ShiftType.ward},
            ],
        )
        assignment_id = sched.assignments[0].id
        resp = client.delete(f"/schedules/{sched.id}/assignments/{assignment_id}")
        assert resp.status_code == 204

        # 削除後に再取得で0件
        resp2 = client.get("/schedules/", params={"year_month": "2025-01"})
        assert len(resp2.json()["assignments"]) == 0

    def test_delete_assignment_not_found(
        self,
        client: TestClient,
        create_schedule: Callable[..., Any],
    ) -> None:
        sched = create_schedule(year_month="2025-01")
        resp = client.delete(f"/schedules/{sched.id}/assignments/9999")
        assert resp.status_code == 404


class TestGenerateSchedule:
    def test_generate_schedule_mocked(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
    ) -> None:
        m = create_member(name="生成テスト")
        mock_assignments = [
            {
                "member_id": m.id,
                "member_name": m.name,
                "date": datetime.date(2025, 1, 6),
                "shift_type": ShiftType.ward,
            },
            {
                "member_id": m.id,
                "member_name": m.name,
                "date": datetime.date(2025, 1, 7),
                "shift_type": ShiftType.day_off,
            },
        ]
        mock_unfulfilled: list[dict[str, object]] = []

        with patch("solver.generator.generate_shift", return_value=(mock_assignments, mock_unfulfilled)):
            resp = client.post("/schedules/generate", json={"year_month": "2025-01"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["schedule"]["year_month"] == "2025-01"
        assert len(data["schedule"]["assignments"]) == 2
        assert data["unfulfilled_requests"] == []

    def test_generate_schedule_solver_error(self, client: TestClient) -> None:
        with patch("solver.generator.generate_shift", side_effect=RuntimeError("制約充足不能")):
            resp = client.post("/schedules/generate", json={"year_month": "2025-01"})
        assert resp.status_code == 422
        assert "制約充足不能" in resp.json()["detail"]


class TestGetSummary:
    def test_get_summary(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        m = create_member(name="サマリーテスト")
        sched = create_schedule(
            year_month="2025-01",
            assignments=[
                {"member_id": m.id, "date": datetime.date(2025, 1, 6), "shift_type": ShiftType.ward},
                {"member_id": m.id, "date": datetime.date(2025, 1, 7), "shift_type": ShiftType.night},
                {"member_id": m.id, "date": datetime.date(2025, 1, 8), "shift_type": ShiftType.day_off},
                # 2025-01-12 is Sunday
                {"member_id": m.id, "date": datetime.date(2025, 1, 12), "shift_type": ShiftType.ward},
            ],
        )
        resp = client.get(f"/schedules/{sched.id}/summary")
        assert resp.status_code == 200
        data = resp.json()
        summary = next(s for s in data["members"] if s["member_id"] == m.id)
        assert summary["working_days"] == 3
        assert summary["night_shift_count"] == 1
        assert summary["day_off_count"] == 1
        assert summary["holiday_work_count"] == 1

    def test_get_summary_with_requests(
        self,
        client: TestClient,
        db_session: Session,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        m = create_member(name="希望休サマリー")
        db_session.add(ShiftRequest(member_id=m.id, year_month="2025-01", date=datetime.date(2025, 1, 8)))
        db_session.add(ShiftRequest(member_id=m.id, year_month="2025-01", date=datetime.date(2025, 1, 9)))
        db_session.commit()

        sched = create_schedule(
            year_month="2025-01",
            assignments=[
                {"member_id": m.id, "date": datetime.date(2025, 1, 8), "shift_type": ShiftType.day_off},
                {"member_id": m.id, "date": datetime.date(2025, 1, 9), "shift_type": ShiftType.ward},
            ],
        )
        resp = client.get(f"/schedules/{sched.id}/summary")
        assert resp.status_code == 200
        summary = next(s for s in resp.json()["members"] if s["member_id"] == m.id)
        assert summary["request_total"] == 2
        assert summary["request_fulfilled"] == 1


class TestGetPdf:
    def test_get_pdf(
        self,
        client: TestClient,
        create_member: Callable[..., Member],
        create_schedule: Callable[..., Any],
    ) -> None:
        m = create_member(name="PDF テスト")
        sched = create_schedule(
            year_month="2025-01",
            assignments=[
                {"member_id": m.id, "date": datetime.date(2025, 1, 6), "shift_type": ShiftType.ward},
            ],
        )
        resp = client.get(f"/schedules/{sched.id}/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:5] == b"%PDF-"
