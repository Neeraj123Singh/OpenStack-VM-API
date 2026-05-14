from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_vm_crud_and_actions(client: TestClient) -> None:
    create = client.post(
        "/api/v1/vms",
        json={
            "name": "test-vm",
            "image_id": "img-1",
            "flavor_id": "flv-1",
        },
    )
    assert create.status_code == 201
    body = create.json()
    vm_id = body["id"]
    assert body["name"] == "test-vm"
    assert body["status"] in ("BUILD", "ACTIVE")

    listed = client.get("/api/v1/vms")
    assert listed.status_code == 200
    data = listed.json()
    assert data["total"] >= 1
    assert any(v["id"] == vm_id for v in data["vms"])

    got = client.get(f"/api/v1/vms/{vm_id}")
    assert got.status_code == 200

    st = client.post(f"/api/v1/vms/{vm_id}/actions/stop")
    assert st.status_code == 200
    assert client.get(f"/api/v1/vms/{vm_id}").json()["status"] == "STOPPED"

    st2 = client.post(f"/api/v1/vms/{vm_id}/actions/start")
    assert st2.status_code == 200

    rb = client.post(f"/api/v1/vms/{vm_id}/actions/reboot")
    assert rb.status_code == 200

    missing = client.post("/api/v1/vms/00000000-0000-0000-0000-000000000000/actions/stop")
    assert missing.status_code == 404

    deleted = client.delete(f"/api/v1/vms/{vm_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/vms/{vm_id}").status_code == 404
