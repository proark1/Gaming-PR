from app.seed.outlets import GAMING_OUTLETS, seed_outlets
from app.config import SUPPORTED_LANGUAGES


def test_all_languages_have_outlets():
    """Ensure every supported language has at least 3 outlets."""
    languages_with_outlets = set()
    outlet_counts = {}
    for outlet in GAMING_OUTLETS:
        lang = outlet["language"]
        languages_with_outlets.add(lang)
        outlet_counts[lang] = outlet_counts.get(lang, 0) + 1

    for lang_code in SUPPORTED_LANGUAGES:
        assert lang_code in languages_with_outlets, f"No outlets for language: {lang_code}"
        assert outlet_counts[lang_code] >= 3, f"Only {outlet_counts[lang_code]} outlets for {lang_code}"


def test_no_duplicate_urls():
    urls = [o["url"] for o in GAMING_OUTLETS]
    assert len(urls) == len(set(urls)), "Duplicate outlet URLs found"


def test_seed_outlets(db):
    added = seed_outlets(db)
    assert added == len(GAMING_OUTLETS)

    # Run again - should be idempotent
    added_again = seed_outlets(db)
    assert added_again == 0


def test_outlet_crud(client, auth_header):
    response = client.post("/api/outlets/", json={
        "name": "Test Outlet",
        "url": "https://testoutlet.example.com",
        "language": "en",
        "region": "US",
        "scraper_type": "generic",
    }, headers=auth_header)
    assert response.status_code == 201
    outlet_id = response.json()["id"]

    response = client.get(f"/api/outlets/{outlet_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Outlet"

    response = client.patch(f"/api/outlets/{outlet_id}", json={"priority": 1}, headers=auth_header)
    assert response.status_code == 200

    response = client.delete(f"/api/outlets/{outlet_id}", headers=auth_header)
    assert response.status_code == 204


def test_outlet_duplicate_rejected(client, auth_header):
    client.post("/api/outlets/", json={
        "name": "Outlet A",
        "url": "https://unique-outlet.example.com",
        "language": "en",
        "region": "US",
    }, headers=auth_header)
    response = client.post("/api/outlets/", json={
        "name": "Outlet B",
        "url": "https://unique-outlet.example.com",
        "language": "en",
        "region": "US",
    }, headers=auth_header)
    assert response.status_code == 409


def test_outlet_invalid_language(client, auth_header):
    response = client.post("/api/outlets/", json={
        "name": "Bad Lang",
        "url": "https://badlang.example.com",
        "language": "xx",
        "region": "XX",
    }, headers=auth_header)
    assert response.status_code == 400
