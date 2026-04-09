from unittest.mock import MagicMock
import pytest
from app.services.integrations import IntegrationService
from app.domain.models import Integration

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def service(mock_repo):
    return IntegrationService(integration_repository=mock_repo)

def test_get_integrations(service, mock_repo):
    expected = [Integration(id="1")]
    mock_repo.get_all.return_value = expected
    assert service.get_integrations("schema") == expected

def test_get_integration_by_id(service, mock_repo):
    expected = Integration(id="1")
    mock_repo.get_by_id.return_value = expected
    assert service.get_integration_by_id("1", "schema") == expected

def test_create_integration(service, mock_repo):
    expected = Integration(id="1")
    mock_repo.add.return_value = expected
    assert service.create_integration("type", "endpoint", "key", "schema") == expected

def test_delete_integration_by_id(service, mock_repo):
    service.delete_integration_by_id("1", "schema")
    mock_repo.delete_by_id.assert_called_once_with("1", "schema")
