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
