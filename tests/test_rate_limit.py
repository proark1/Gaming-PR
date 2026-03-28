"""Tests for rate limiting on auth endpoints."""


def test_login_rate_limit(client):
    """Login should return 429 after too many attempts."""
    for _ in range(10):
        client.post("/api/auth/login", json={"username": "bad", "password": "badpass12"})
    resp = client.post("/api/auth/login", json={"username": "bad", "password": "badpass12"})
    assert resp.status_code == 429
    assert "too many" in resp.json()["detail"].lower()


def test_register_rate_limit(client):
    """Register should return 429 after too many attempts."""
    for i in range(5):
        client.post("/api/auth/register", json={
            "username": f"spam{i}", "email": f"spam{i}@test.com", "password": "testpass1"
        })
    resp = client.post("/api/auth/register", json={
        "username": "spam99", "email": "spam99@test.com", "password": "testpass1"
    })
    assert resp.status_code == 429
