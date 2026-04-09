import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


def auth_headers() -> dict:
    return {"Authorization": f"Bearer {os.environ['ACCESS_TOKEN']}"}


def create_integration(client) -> str:
    response = client.post(
        "/integrations/create",
        headers=auth_headers(),
        json={
            "integration_type": "ollama_api_v1",
            "api_endpoint": "http://localhost:21434",
            "api_key": "test-key",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


class TestLanguageModelsCRUD:
    integration_id: str = None
    created_id: str = None

    def test_setup_integration(self, client):
        TestLanguageModelsCRUD.integration_id = create_integration(client)
        assert TestLanguageModelsCRUD.integration_id is not None

    def test_list_empty(self, client):
        response = client.get("/llms/list", headers=auth_headers())
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_language_model(self, client):
        assert TestLanguageModelsCRUD.integration_id is not None
        response = client.post(
            "/llms/create",
            headers=auth_headers(),
            json={
                "integration_id": TestLanguageModelsCRUD.integration_id,
                "language_model_tag": "bge-m3",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["language_model_tag"] == "bge-m3"
        assert data["integration_id"] == TestLanguageModelsCRUD.integration_id
        TestLanguageModelsCRUD.created_id = data["id"]

    def test_list_contains_created(self, client):
        assert TestLanguageModelsCRUD.created_id is not None
        response = client.get("/llms/list", headers=auth_headers())
        assert response.status_code == 200
        ids = [item["id"] for item in response.json()]
        assert TestLanguageModelsCRUD.created_id in ids

    def test_get_by_id(self, client):
        assert TestLanguageModelsCRUD.created_id is not None
        response = client.get(
            f"/llms/{TestLanguageModelsCRUD.created_id}",
            headers=auth_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TestLanguageModelsCRUD.created_id
        assert "lm_settings" in data

    def test_get_nonexistent_returns_404(self, client):
        response = client.get(
            "/llms/nonexistent-id",
            headers=auth_headers(),
        )
        assert response.status_code == 404

    def test_create_invalid_tag_returns_400(self, client):
        assert TestLanguageModelsCRUD.integration_id is not None
        response = client.post(
            "/llms/create",
            headers=auth_headers(),
            json={
                "integration_id": TestLanguageModelsCRUD.integration_id,
                "language_model_tag": "invalid tag with spaces",
            },
        )
        assert response.status_code == 400

    def test_update_language_model(self, client):
        assert TestLanguageModelsCRUD.created_id is not None
        response = client.post(
            "/llms/update",
            headers=auth_headers(),
            json={
                "language_model_id": TestLanguageModelsCRUD.created_id,
                "language_model_tag": "bge-m3-updated",
                "integration_id": TestLanguageModelsCRUD.integration_id,
            },
        )
        assert response.status_code == 200
        assert response.json()["language_model_tag"] == "bge-m3-updated"

    def test_update_setting(self, client):
        assert TestLanguageModelsCRUD.created_id is not None
        response = client.post(
            "/llms/update_setting",
            headers=auth_headers(),
            json={
                "language_model_id": TestLanguageModelsCRUD.created_id,
                "setting_key": "embeddings",
                "setting_value": "nomic-embed-text",
            },
        )
        assert response.status_code == 200
        settings = response.json()["lm_settings"]
        setting = next((s for s in settings if s["setting_key"] == "embeddings"), None)
        assert setting is not None
        assert setting["setting_value"] == "nomic-embed-text"

    def test_delete_language_model(self, client):
        assert TestLanguageModelsCRUD.created_id is not None
        response = client.delete(
            f"/llms/delete/{TestLanguageModelsCRUD.created_id}",
            headers=auth_headers(),
        )
        assert response.status_code == 204

    def test_cleanup_integration(self, client):
        assert TestLanguageModelsCRUD.integration_id is not None
        response = client.delete(
            f"/integrations/delete/{TestLanguageModelsCRUD.integration_id}",
            headers=auth_headers(),
        )
        assert response.status_code == 204
