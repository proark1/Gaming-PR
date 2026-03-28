"""Tests for monitoring dashboard and health endpoints."""


def test_health_endpoint(client):
    resp = client.get("/api/monitoring/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded", "unhealthy")
    assert "database" in data
    assert "timestamp" in data


def test_dashboard_endpoint(client):
    resp = client.get("/api/monitoring/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "overview" in data
    assert "language_coverage" in data
    assert "top_outlets" in data
    assert "failing_outlets" in data
    assert "recent_jobs" in data
    assert "system" in data
    assert data["overview"]["total_outlets"] >= 0


def test_dashboard_system_config(client):
    resp = client.get("/api/monitoring/dashboard")
    system = resp.json()["system"]
    assert "scrape_interval_minutes" in system
    assert "concurrency" in system
    assert "full_content_extraction" in system
