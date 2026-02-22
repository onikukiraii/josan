from collections.abc import Callable

from fastapi.testclient import TestClient

from entity.member import Member


class TestGetMembers:
    def test_get_members_empty(self, client: TestClient) -> None:
        resp = client.get("/members/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_members_with_data(self, client: TestClient, create_member: Callable[..., Member]) -> None:
        create_member(name="田中太郎")
        create_member(name="鈴木花子")
        resp = client.get("/members/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["name"] == "田中太郎"
        assert data[1]["name"] == "鈴木花子"


class TestCreateMember:
    def test_create_member_minimal(self, client: TestClient) -> None:
        resp = client.post(
            "/members/",
            json={
                "name": "新規メンバー",
                "qualification": "nurse",
                "employment_type": "full_time",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "新規メンバー"
        assert data["max_night_shifts"] == 4
        assert data["night_shift_deduction_balance"] == 0
        assert data["capabilities"] == []

    def test_create_member_with_capabilities(self, client: TestClient) -> None:
        resp = client.post(
            "/members/",
            json={
                "name": "能力持ち",
                "qualification": "midwife",
                "employment_type": "full_time",
                "capabilities": ["day_shift", "night_shift", "ward_staff"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert set(data["capabilities"]) == {"day_shift", "night_shift", "ward_staff"}


class TestGetMemberById:
    def test_get_member_by_id(self, client: TestClient, create_member: Callable[..., Member]) -> None:
        m = create_member(name="特定メンバー")
        resp = client.get(f"/members/{m.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "特定メンバー"

    def test_get_member_not_found(self, client: TestClient) -> None:
        resp = client.get("/members/9999")
        assert resp.status_code == 404


class TestUpdateMember:
    def test_update_member_name(self, client: TestClient, create_member: Callable[..., Member]) -> None:
        m = create_member(name="旧名前")
        resp = client.put(f"/members/{m.id}", json={"name": "新名前"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "新名前"
        assert data["qualification"] == "nurse"

    def test_update_member_capabilities(self, client: TestClient, create_member: Callable[..., Member]) -> None:
        m = create_member(name="能力変更", capabilities=["day_shift"])
        resp = client.put(f"/members/{m.id}", json={"capabilities": ["night_shift", "ward_leader"]})
        assert resp.status_code == 200
        assert set(resp.json()["capabilities"]) == {"night_shift", "ward_leader"}

    def test_update_member_partial(self, client: TestClient, create_member: Callable[..., Member]) -> None:
        m = create_member(name="部分更新", max_night_shifts=3)
        resp = client.put(f"/members/{m.id}", json={"max_night_shifts": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert data["max_night_shifts"] == 2
        assert data["name"] == "部分更新"


class TestDeleteMember:
    def test_delete_member(self, client: TestClient, create_member: Callable[..., Member]) -> None:
        m = create_member(name="削除対象")
        resp = client.delete(f"/members/{m.id}")
        assert resp.status_code == 200
        assert resp.json() == {"detail": "Deleted"}
        assert client.get(f"/members/{m.id}").status_code == 404

    def test_delete_member_not_found(self, client: TestClient) -> None:
        resp = client.delete("/members/9999")
        assert resp.status_code == 404
