from fastapi.testclient import TestClient

from entity.member import Member


class TestGetNgPairs:
    def test_get_ng_pairs_empty(self, client: TestClient) -> None:
        resp = client.get("/ng-pairs/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_ng_pairs_with_data(self, client: TestClient, sample_members: list[Member]) -> None:
        m1, m2 = sample_members
        client.post("/ng-pairs/", json={"member_id_1": m1.id, "member_id_2": m2.id})
        resp = client.get("/ng-pairs/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestCreateNgPair:
    def test_create_ng_pair(self, client: TestClient, sample_members: list[Member]) -> None:
        m1, m2 = sample_members
        resp = client.post("/ng-pairs/", json={"member_id_1": m1.id, "member_id_2": m2.id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["member_name_1"] == m1.name
        assert data["member_name_2"] == m2.name

    def test_create_ng_pair_normalized_order(self, client: TestClient, sample_members: list[Member]) -> None:
        m1, m2 = sample_members
        resp = client.post("/ng-pairs/", json={"member_id_1": m2.id, "member_id_2": m1.id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["member_id_1"] < data["member_id_2"]

    def test_create_ng_pair_same_member(self, client: TestClient, sample_members: list[Member]) -> None:
        m1 = sample_members[0]
        resp = client.post("/ng-pairs/", json={"member_id_1": m1.id, "member_id_2": m1.id})
        assert resp.status_code == 400

    def test_create_ng_pair_duplicate(self, client: TestClient, sample_members: list[Member]) -> None:
        m1, m2 = sample_members
        client.post("/ng-pairs/", json={"member_id_1": m1.id, "member_id_2": m2.id})
        resp = client.post("/ng-pairs/", json={"member_id_1": m1.id, "member_id_2": m2.id})
        assert resp.status_code == 409

    def test_create_ng_pair_member_not_found(self, client: TestClient, sample_members: list[Member]) -> None:
        m1 = sample_members[0]
        resp = client.post("/ng-pairs/", json={"member_id_1": m1.id, "member_id_2": 9999})
        assert resp.status_code == 404


class TestDeleteNgPair:
    def test_delete_ng_pair(self, client: TestClient, sample_members: list[Member]) -> None:
        m1, m2 = sample_members
        create_resp = client.post("/ng-pairs/", json={"member_id_1": m1.id, "member_id_2": m2.id})
        pair_id = create_resp.json()["id"]
        resp = client.delete(f"/ng-pairs/{pair_id}")
        assert resp.status_code == 200
        assert resp.json() == {"detail": "Deleted"}
        assert client.get("/ng-pairs/").json() == []
