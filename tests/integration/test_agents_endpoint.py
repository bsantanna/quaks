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


def create_language_model(client, integration_id: str) -> str:
    response = client.post(
        "/llms/create",
        headers=auth_headers(),
        json={
            "integration_id": integration_id,
            "language_model_tag": "bge-m3",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


class TestAgentsCRUD:
    integration_id: str = None
    language_model_id: str = None
    created_id: str = None

    def test_setup_prerequisites(self, client):
        TestAgentsCRUD.integration_id = create_integration(client)
        TestAgentsCRUD.language_model_id = create_language_model(
            client, TestAgentsCRUD.integration_id
        )
        assert TestAgentsCRUD.language_model_id is not None

    def test_list_empty(self, client):
        response = client.get("/agents/list", headers=auth_headers())
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_agent(self, client):
        assert TestAgentsCRUD.language_model_id is not None
        response = client.post(
            "/agents/create",
            headers=auth_headers(),
            json={
                "agent_name": "test-echo-agent",
                "agent_type": "test_echo",
                "language_model_id": TestAgentsCRUD.language_model_id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["agent_name"] == "test-echo-agent"
        assert data["agent_type"] == "test_echo"
        TestAgentsCRUD.created_id = data["id"]

    def test_list_contains_created(self, client):
        assert TestAgentsCRUD.created_id is not None
        response = client.get("/agents/list", headers=auth_headers())
        assert response.status_code == 200
        ids = [item["id"] for item in response.json()]
        assert TestAgentsCRUD.created_id in ids

    def test_get_by_id(self, client):
        assert TestAgentsCRUD.created_id is not None
        response = client.get(
            f"/agents/{TestAgentsCRUD.created_id}",
            headers=auth_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TestAgentsCRUD.created_id
        assert "ag_settings" in data

    def test_get_nonexistent_returns_404(self, client):
        response = client.get("/agents/nonexistent-id", headers=auth_headers())
        assert response.status_code == 404

    def test_create_invalid_type_returns_400(self, client):
        response = client.post(
            "/agents/create",
            headers=auth_headers(),
            json={
                "agent_name": "bad-agent",
                "agent_type": "unknown_type",
                "language_model_id": TestAgentsCRUD.language_model_id,
            },
        )
        assert response.status_code == 400

    def test_update_agent(self, client):
        assert TestAgentsCRUD.created_id is not None
        response = client.post(
            "/agents/update",
            headers=auth_headers(),
            json={
                "agent_id": TestAgentsCRUD.created_id,
                "agent_name": "test-echo-agent-renamed",
                "language_model_id": TestAgentsCRUD.language_model_id,
                "agent_summary": "Updated summary",
            },
        )
        assert response.status_code == 200
        assert response.json()["agent_name"] == "test-echo-agent-renamed"

    def test_update_setting(self, client):
        assert TestAgentsCRUD.created_id is not None
        response = client.post(
            "/agents/update_setting",
            headers=auth_headers(),
            json={
                "agent_id": TestAgentsCRUD.created_id,
                "setting_key": "dummy_setting",
                "setting_value": "updated_value",
            },
        )
        assert response.status_code == 200
        settings = response.json()["ag_settings"]
        setting = next(
            (s for s in settings if s["setting_key"] == "dummy_setting"), None
        )
        assert setting is not None
        assert setting["setting_value"] == "updated_value"

    def test_delete_agent(self, client):
        assert TestAgentsCRUD.created_id is not None
        response = client.delete(
            f"/agents/delete/{TestAgentsCRUD.created_id}",
            headers=auth_headers(),
        )
        assert response.status_code == 204

    def test_cleanup_prerequisites(self, client):
        if TestAgentsCRUD.language_model_id:
            client.delete(
                f"/llms/delete/{TestAgentsCRUD.language_model_id}",
                headers=auth_headers(),
            )
        if TestAgentsCRUD.integration_id:
            client.delete(
                f"/integrations/delete/{TestAgentsCRUD.integration_id}",
                headers=auth_headers(),
            )
