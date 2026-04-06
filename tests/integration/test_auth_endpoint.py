import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


def auth_headers() -> dict:
    return {"Authorization": f"Bearer {os.environ['ACCESS_TOKEN']}"}


def test_login_success(client):
    response = client.post(
        "/auth/login",
        json={"username": "foo", "password": "bar"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"]
    assert data["refresh_token"]


def test_login_invalid_credentials_returns_401(client):
    response = client.post(
        "/auth/login",
        json={"username": "foo", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_renew_token(client):
    login = client.post(
        "/auth/login",
        json={"username": "foo", "password": "bar"},
    )
    assert login.status_code == 201
    refresh_token = login.json()["refresh_token"]

    response = client.post(
        "/auth/renew",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["access_token"]


def test_renew_with_invalid_token_returns_401(client):
    response = client.post(
        "/auth/renew",
        json={"refresh_token": "not-a-valid-token"},
    )
    assert response.status_code == 401


def test_get_profile(client):
    response = client.get("/auth/profile", headers=auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert "email" in data


def test_get_profile_unauthenticated_returns_401(client):
    response = client.get("/auth/profile")
    assert response.status_code == 401
