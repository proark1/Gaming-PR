"""Tests for authentication: registration and login."""


def test_register_success(client):
    resp = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["is_active"] is True


def test_register_duplicate_username(client):
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test1@example.com",
        "password": "securepass123",
    })
    resp = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test2@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 400
    assert "Username already taken" in resp.json()["detail"]


def test_register_duplicate_email(client):
    client.post("/api/auth/register", json={
        "username": "user1",
        "email": "same@example.com",
        "password": "securepass123",
    })
    resp = client.post("/api/auth/register", json={
        "username": "user2",
        "email": "same@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 400
    assert "Email already registered" in resp.json()["detail"]


def test_register_short_password(client):
    resp = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "short",
    })
    assert resp.status_code == 400
    assert "8 characters" in resp.json()["detail"]


def test_register_invalid_email(client):
    resp = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "not-an-email",
        "password": "securepass123",
    })
    assert resp.status_code == 422


def test_login_success(client):
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
    })
    resp = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "securepass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["user"]["username"] == "testuser"


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
    })
    resp = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401
    assert "Invalid username or password" in resp.json()["detail"]


def test_login_nonexistent_user(client):
    resp = client.post("/api/auth/login", json={
        "username": "nobody",
        "password": "securepass123",
    })
    assert resp.status_code == 401


def test_me_with_valid_token(client):
    resp = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
    })
    token = resp.json()["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_me_without_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_invalid_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


# ── Route protection tests ──

def _auth_header(client):
    resp = client.post("/api/auth/register", json={
        "username": "authuser",
        "email": "auth@example.com",
        "password": "securepass123",
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# Articles
def test_create_article_requires_auth(client):
    resp = client.post("/api/articles/", json={"title": "T", "body": "B"})
    assert resp.status_code == 401


def test_create_article_with_auth(client):
    resp = client.post("/api/articles/", json={"title": "T", "body": "B"}, headers=_auth_header(client))
    assert resp.status_code == 201


def test_update_article_requires_auth(client):
    assert client.put("/api/articles/999", json={"title": "X"}).status_code == 401


def test_delete_article_requires_auth(client):
    assert client.delete("/api/articles/999").status_code == 401


def test_list_articles_public(client):
    assert client.get("/api/articles/").status_code == 200


# Outlets
def test_create_outlet_requires_auth(client):
    resp = client.post("/api/outlets/", json={"name": "X", "url": "http://x.com", "language": "en"})
    assert resp.status_code == 401


def test_update_outlet_requires_auth(client):
    assert client.patch("/api/outlets/999", json={"name": "Y"}).status_code == 401


def test_delete_outlet_requires_auth(client):
    assert client.delete("/api/outlets/999").status_code == 401


def test_list_outlets_public(client):
    assert client.get("/api/outlets/").status_code == 200


# Scraper
def test_run_scraper_requires_auth(client):
    assert client.post("/api/scraper/run").status_code == 401


def test_run_single_scraper_requires_auth(client):
    assert client.post("/api/scraper/run/1").status_code == 401


def test_reset_circuit_breaker_requires_auth(client):
    assert client.post("/api/scraper/circuit-breakers/1/reset").status_code == 401


def test_process_retries_requires_auth(client):
    assert client.post("/api/scraper/retry-queue/process").status_code == 401


def test_scraper_stats_public(client):
    assert client.get("/api/scraper/stats").status_code == 200


# Webhooks
def test_create_webhook_requires_auth(client):
    resp = client.post("/api/webhooks/", json={"name": "W", "url": "http://x.com"})
    assert resp.status_code == 401


def test_delete_webhook_requires_auth(client):
    assert client.delete("/api/webhooks/999").status_code == 401


def test_toggle_webhook_requires_auth(client):
    assert client.post("/api/webhooks/999/toggle").status_code == 401


def test_test_webhook_requires_auth(client):
    assert client.post("/api/webhooks/999/test").status_code == 401


def test_list_webhooks_public(client):
    assert client.get("/api/webhooks/").status_code == 200


# Email
def test_add_domain_requires_auth(client):
    resp = client.post("/api/email/domains", json={"domain": "x.com"})
    assert resp.status_code == 401


def test_delete_domain_requires_auth(client):
    assert client.delete("/api/email/domains/999").status_code == 401


def test_verify_domain_requires_auth(client):
    assert client.post("/api/email/domains/999/verify").status_code == 401


def test_send_email_requires_auth(client):
    resp = client.post("/api/email/send", json={"domain_id": 1, "to": ["a@b.com"], "subject": "Hi", "html": "<p>Hi</p>"})
    assert resp.status_code == 401


def test_send_batch_requires_auth(client):
    resp = client.post("/api/email/send/batch", json={"domain_id": 1, "emails": []})
    assert resp.status_code == 401


def test_list_emails_public(client):
    assert client.get("/api/email/emails").status_code == 200


# Translations
def test_retry_translations_requires_auth(client):
    assert client.post("/api/articles/999/translations/retry").status_code == 401


def test_list_translations_public(client):
    # Create an article first with auth, then verify translations list is public
    headers = _auth_header(client)
    resp = client.post("/api/articles/", json={"title": "T", "body": "B"}, headers=headers)
    article_id = resp.json()["id"]
    assert client.get(f"/api/articles/{article_id}/translations/").status_code == 200
