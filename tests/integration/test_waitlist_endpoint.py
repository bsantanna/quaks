import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


def test_waitlist_register(client):
    unique = uuid.uuid4().hex[:8]
    response = client.post(
        "/waitlist",
        json={
            "email": f"test-{unique}@example.com",
            "first_name": "Test",
            "last_name": "User",
            "username": f"testuser-{unique}",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "registered"


def test_waitlist_duplicate_email_returns_409(client):
    unique = uuid.uuid4().hex[:8]
    payload = {
        "email": f"dup-{unique}@example.com",
        "first_name": "Dup",
        "last_name": "User",
        "username": f"dupuser-{unique}",
    }
    client.post("/waitlist", json=payload)
    response = client.post("/waitlist", json=payload)
    assert response.status_code == 409


def test_waitlist_invalid_email_returns_422(client):
    response = client.post(
        "/waitlist",
        json={
            "email": "not-an-email",
            "first_name": "Bad",
            "last_name": "Email",
            "username": "bademail",
        },
    )
    assert response.status_code == 422


def test_waitlist_short_username_returns_422(client):
    response = client.post(
        "/waitlist",
        json={
            "email": "short@example.com",
            "first_name": "Short",
            "last_name": "Name",
            "username": "ab",
        },
    )
    assert response.status_code == 422
