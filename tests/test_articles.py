from unittest.mock import patch


def test_create_article(client, auth_header):
    with patch("app.routers.articles._run_translation"):
        response = client.post("/api/articles/", json={
            "title": "New Game Release",
            "body": "An exciting new game has been announced for 2026.",
            "source_language": "en",
            "author_name": "Test Author",
        }, headers=auth_header)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Game Release"
    assert data["source_language"] == "en"
    assert "id" in data


def test_list_articles(client, auth_header):
    with patch("app.routers.articles._run_translation"):
        client.post("/api/articles/", json={"title": "Article 1", "body": "Body 1"}, headers=auth_header)
        client.post("/api/articles/", json={"title": "Article 2", "body": "Body 2"}, headers=auth_header)
    response = client.get("/api/articles/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_article(client, auth_header):
    with patch("app.routers.articles._run_translation"):
        create_resp = client.post("/api/articles/", json={
            "title": "Test Article",
            "body": "Test body content.",
        }, headers=auth_header)
    article_id = create_resp.json()["id"]
    response = client.get(f"/api/articles/{article_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Article"


def test_update_article(client, auth_header):
    with patch("app.routers.articles._run_translation"):
        create_resp = client.post("/api/articles/", json={
            "title": "Original Title",
            "body": "Original body.",
        }, headers=auth_header)
        article_id = create_resp.json()["id"]
        response = client.put(f"/api/articles/{article_id}", json={
            "title": "Updated Title",
        }, headers=auth_header)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


def test_delete_article(client, auth_header):
    with patch("app.routers.articles._run_translation"):
        create_resp = client.post("/api/articles/", json={
            "title": "To Delete",
            "body": "Will be deleted.",
        }, headers=auth_header)
    article_id = create_resp.json()["id"]
    response = client.delete(f"/api/articles/{article_id}", headers=auth_header)
    assert response.status_code == 204
    response = client.get(f"/api/articles/{article_id}")
    assert response.status_code == 404


def test_article_not_found(client):
    response = client.get("/api/articles/9999")
    assert response.status_code == 404
