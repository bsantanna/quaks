from unittest.mock import patch, MagicMock
import pytest
import requests
from app.services.auth import AuthService
from app.domain.exceptions.base import AuthenticationError

@pytest.fixture
def service():
    return AuthService(
        enabled=True,
        url="http://auth",
        realm="realm",
        client_id="client",
        client_secret="secret"
    )

@patch("requests.post")
def test_login_success(mock_post, service):
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "at", "refresh_token": "rt"}
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = service.login("user", "pass")

    assert result.access_token == "at"
    assert result.refresh_token == "rt"
    mock_post.assert_called_once()

@patch("requests.post")
def test_login_failure(mock_post, service):
    mock_post.side_effect = requests.exceptions.RequestException("error")

    with pytest.raises(AuthenticationError):
        service.login("user", "pass")

@patch("requests.post")
def test_renew_success(mock_post, service):
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "at-new", "refresh_token": "rt-new"}
    mock_post.return_value = mock_response

    result = service.renew("rt-old")

    assert result.access_token == "at-new"
    assert result.refresh_token == "rt-new"

@patch("requests.post")
def test_exchange_success(mock_post, service):
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "at", "refresh_token": "rt"}
    mock_post.return_value = mock_response

    result = service.exchange("code", "verifier", "uri")

    assert result.access_token == "at"
    assert result.refresh_token == "rt"

@patch("requests.post")
@patch("requests.get")
def test_get_user_profile_success(mock_get, mock_post, service):
    # Service account token
    mock_post_resp = MagicMock()
    mock_post_resp.json.return_value = {"access_token": "sa-token"}
    mock_post.return_value = mock_post_resp

    # Get user profile
    mock_get_resp = MagicMock()
    mock_get_resp.json.return_value = {
        "username": "user1",
        "email": "user1@test.com",
        "firstName": "First",
        "lastName": "Last"
    }
    mock_get.return_value = mock_get_resp

    result = service.get_user_profile("id_uuid")

    assert result.username == "user1"
    assert result.email == "user1@test.com"
    assert result.first_name == "First"
    assert result.last_name == "Last"

@patch("requests.post")
@patch("requests.put")
def test_update_user_profile_success(mock_put, mock_post, service):
    # Service account token
    mock_post_resp = MagicMock()
    mock_post_resp.json.return_value = {"access_token": "sa-token"}
    mock_post.return_value = mock_post_resp

    # Put user profile
    mock_put_resp = MagicMock()
    mock_put_resp.status_code = 204
    mock_put.return_value = mock_put_resp

    result = service.update_user_profile("id_uuid", "user1", "user1@test.com", "First", "Last")

    assert result.username == "user1"
    assert result.email == "user1@test.com"

@patch("requests.post")
@patch("requests.put")
def test_update_user_profile_conflict(mock_put, mock_post, service):
    # Service account token
    mock_post_resp = MagicMock()
    mock_post_resp.json.return_value = {"access_token": "sa-token"}
    mock_post.return_value = mock_post_resp

    # Put user profile conflict
    mock_put_resp = MagicMock()
    mock_put_resp.status_code = 409
    mock_put_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_put_resp)
    mock_put.return_value = mock_put_resp

    with pytest.raises(AuthenticationError) as excinfo:
        service.update_user_profile("id_uuid", "user1", "user1@test.com", "First", "Last")
    
    assert "409" in str(excinfo.value)
