"""Tests for admin-only access control."""

from app.services.auth_service import seed_admin_user, hash_password
from app.models.user import User


def _make_admin(db, client):
    """Create an admin user and return auth header."""
    user = User(username="admin", email="admin@test.com", hashed_password=hash_password("adminpass1"), is_admin=True)
    db.add(user)
    db.commit()
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "adminpass1"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_regular_user_cannot_update_outlet(client, auth_header, db):
    from app.models.outlet import GamingOutlet
    outlet = GamingOutlet(name="Test", url="https://test.com", language="en", region="US", scraper_type="rss")
    db.add(outlet)
    db.commit()
    db.refresh(outlet)
    resp = client.patch(f"/api/outlets/{outlet.id}", json={"description": "hacked"}, headers=auth_header)
    assert resp.status_code == 403


def test_admin_can_update_outlet(client, db):
    from app.models.outlet import GamingOutlet
    admin_header = _make_admin(db, client)
    outlet = GamingOutlet(name="Test", url="https://test2.com", language="en", region="US", scraper_type="rss")
    db.add(outlet)
    db.commit()
    db.refresh(outlet)
    resp = client.patch(f"/api/outlets/{outlet.id}", json={"description": "updated"}, headers=admin_header)
    assert resp.status_code == 200
    assert resp.json()["description"] == "updated"


def test_regular_user_cannot_delete_outlet(client, auth_header, db):
    from app.models.outlet import GamingOutlet
    outlet = GamingOutlet(name="Test", url="https://test3.com", language="en", region="US", scraper_type="rss")
    db.add(outlet)
    db.commit()
    db.refresh(outlet)
    resp = client.delete(f"/api/outlets/{outlet.id}", headers=auth_header)
    assert resp.status_code == 403


def test_seed_admin_user_dedup(db):
    """seed_admin_user should not crash on duplicate username."""
    u1 = seed_admin_user(db, email="one@test.com", username="admin_dup")
    u2 = seed_admin_user(db, email="two@test.com", username="admin_dup")
    assert u1.username == "admin_dup"
    assert u2.username == "admin_dup_1"


def test_deactivated_user_rejected(client, db):
    user = User(username="inactive", email="inactive@test.com", hashed_password=hash_password("testpass1"), is_active=False)
    db.add(user)
    db.commit()
    resp = client.post("/api/auth/login", json={"username": "inactive", "password": "testpass1"})
    assert resp.status_code == 403
