import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


def auth_headers() -> dict:
    return {"Authorization": f"Bearer {os.environ['ACCESS_TOKEN']}"}


class TestIntegrationsCRUD:
    created_id: str = None

    def test_list_empty(self, client):
        response = client.get("/integrations/list", headers=auth_headers())
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_integration(self, client):
        response = client.post(
            "/integrations/create",
            headers=auth_headers(),
            json={
                "integration_type": "ollama_api_v1",
                "api_endpoint": "http://localhost:11434",
                "api_key": "test-key",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["integration_type"] == "ollama_api_v1"
        assert "id" in data
        TestIntegrationsCRUD.created_id = data["id"]

    def test_list_contains_created(self, client):
        assert TestIntegrationsCRUD.created_id is not None
        response = client.get("/integrations/list", headers=auth_headers())
        assert response.status_code == 200
        ids = [item["id"] for item in response.json()]
        assert TestIntegrationsCRUD.created_id in ids

    def test_get_by_id(self, client):
        assert TestIntegrationsCRUD.created_id is not None
        response = client.get(
            f"/integrations/{TestIntegrationsCRUD.created_id}",
            headers=auth_headers(),
        )
        assert response.status_code == 200
        assert response.json()["id"] == TestIntegrationsCRUD.created_id

    def test_get_nonexistent_returns_404(self, client):
        response = client.get(
            "/integrations/nonexistent-id",
            headers=auth_headers(),
        )
        assert response.status_code == 404

    def test_create_invalid_type_returns_400(self, client):
        response = client.post(
            "/integrations/create",
            headers=auth_headers(),
            json={
                "integration_type": "invalid_type",
                "api_endpoint": "http://localhost:11434",
                "api_key": "test-key",
            },
        )
        assert response.status_code == 400

    def test_delete_integration(self, client):
        assert TestIntegrationsCRUD.created_id is not None
        response = client.delete(
            f"/integrations/delete/{TestIntegrationsCRUD.created_id}",
            headers=auth_headers(),
        )
        assert response.status_code == 204

    def test_get_deleted_returns_404(self, client):
        assert TestIntegrationsCRUD.created_id is not None
        response = client.get(
            f"/integrations/{TestIntegrationsCRUD.created_id}",
            headers=auth_headers(),
        )
        assert response.status_code == 404
