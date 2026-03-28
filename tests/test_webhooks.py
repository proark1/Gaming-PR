"""Tests for webhook CRUD and SSRF protection."""


def test_create_webhook(client, auth_header):
    resp = client.post("/api/webhooks/", json={
        "name": "Test Hook",
        "url": "https://hooks.example.com/test",
        "events": ["new_article"],
    }, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Hook"
    assert data["url"] == "https://hooks.example.com/test"
    assert data["is_active"] is True


def test_list_webhooks(client, auth_header):
    client.post("/api/webhooks/", json={
        "name": "Hook 1", "url": "https://example.com/h1",
    }, headers=auth_header)
    resp = client.get("/api/webhooks/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_toggle_webhook(client, auth_header):
    create = client.post("/api/webhooks/", json={
        "name": "Toggle", "url": "https://example.com/toggle",
    }, headers=auth_header)
    wh_id = create.json()["id"]
    resp = client.post(f"/api/webhooks/{wh_id}/toggle", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_delete_webhook(client, auth_header):
    create = client.post("/api/webhooks/", json={
        "name": "Delete", "url": "https://example.com/delete",
    }, headers=auth_header)
    wh_id = create.json()["id"]
    resp = client.delete(f"/api/webhooks/{wh_id}", headers=auth_header)
    assert resp.status_code == 200


def test_ssrf_block_localhost(client, auth_header):
    resp = client.post("/api/webhooks/", json={
        "name": "evil", "url": "http://localhost:5432/",
    }, headers=auth_header)
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["detail"].lower()


def test_ssrf_block_metadata(client, auth_header):
    resp = client.post("/api/webhooks/", json={
        "name": "evil", "url": "http://169.254.169.254/latest/",
    }, headers=auth_header)
    assert resp.status_code == 400


def test_ssrf_block_private_ip(client, auth_header):
    resp = client.post("/api/webhooks/", json={
        "name": "evil", "url": "http://192.168.1.1/admin",
    }, headers=auth_header)
    assert resp.status_code == 400


def test_webhook_requires_auth(client):
    resp = client.post("/api/webhooks/", json={
        "name": "no auth", "url": "https://example.com/test",
    })
    assert resp.status_code == 401
