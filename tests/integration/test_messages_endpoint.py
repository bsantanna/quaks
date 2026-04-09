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
        json={"integration_id": integration_id, "language_model_tag": "bge-m3"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_agent(client, language_model_id: str) -> str:
    response = client.post(
        "/agents/create",
        headers=auth_headers(),
        json={
            "agent_name": "msg-test-agent",
            "agent_type": "test_echo",
            "language_model_id": language_model_id,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


class TestMessagesCRUD:
    integration_id: str = None
    language_model_id: str = None
    agent_id: str = None
    assistant_message_id: str = None

    def test_setup_prerequisites(self, client):
        TestMessagesCRUD.integration_id = create_integration(client)
        TestMessagesCRUD.language_model_id = create_language_model(
            client, TestMessagesCRUD.integration_id
        )
        TestMessagesCRUD.agent_id = create_agent(
            client, TestMessagesCRUD.language_model_id
        )
        assert TestMessagesCRUD.agent_id is not None

    def test_list_messages_empty(self, client):
        assert TestMessagesCRUD.agent_id is not None
        response = client.post(
            "/messages/list",
            headers=auth_headers(),
            json={"agent_id": TestMessagesCRUD.agent_id},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_post_message(self, client):
        assert TestMessagesCRUD.agent_id is not None
        response = client.post(
            "/messages/post",
            headers=auth_headers(),
            json={
                "agent_id": TestMessagesCRUD.agent_id,
                "message_role": "human",
                "message_content": "Hello, echo this!",
                "attachment_id": None,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message_role"] == "assistant"
        assert data["agent_id"] == TestMessagesCRUD.agent_id
        assert "message_content" in data
        TestMessagesCRUD.assistant_message_id = data["id"]

    def test_list_messages_has_entries(self, client):
        assert TestMessagesCRUD.agent_id is not None
        response = client.post(
            "/messages/list",
            headers=auth_headers(),
            json={"agent_id": TestMessagesCRUD.agent_id},
        )
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 2  # human + assistant

    def test_get_message_by_id(self, client):
        assert TestMessagesCRUD.assistant_message_id is not None
        response = client.get(
            f"/messages/{TestMessagesCRUD.assistant_message_id}",
            headers=auth_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TestMessagesCRUD.assistant_message_id
        assert data["message_role"] == "assistant"
        assert "replies_to" in data

    def test_get_message_nonexistent_returns_404(self, client):
        response = client.get("/messages/nonexistent-id", headers=auth_headers())
        assert response.status_code == 404

    def test_post_message_invalid_role_returns_400(self, client):
        assert TestMessagesCRUD.agent_id is not None
        response = client.post(
            "/messages/post",
            headers=auth_headers(),
            json={
                "agent_id": TestMessagesCRUD.agent_id,
                "message_role": "invalid_role",
                "message_content": "Test",
                "attachment_id": None,
            },
        )
        assert response.status_code in (400, 422)

    def test_delete_message(self, client):
        assert TestMessagesCRUD.assistant_message_id is not None
        response = client.delete(
            f"/messages/delete/{TestMessagesCRUD.assistant_message_id}",
            headers=auth_headers(),
        )
        assert response.status_code == 204

    def test_cleanup_prerequisites(self, client):
        if TestMessagesCRUD.agent_id:
            client.delete(
                f"/agents/delete/{TestMessagesCRUD.agent_id}",
                headers=auth_headers(),
            )
        if TestMessagesCRUD.language_model_id:
            client.delete(
                f"/llms/delete/{TestMessagesCRUD.language_model_id}",
                headers=auth_headers(),
            )
        if TestMessagesCRUD.integration_id:
            client.delete(
                f"/integrations/delete/{TestMessagesCRUD.integration_id}",
                headers=auth_headers(),
            )
