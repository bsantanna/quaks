from unittest.mock import MagicMock, patch
import pytest
from app.domain.repositories.integrations import IntegrationRepository, IntegrationNotFoundError
from app.domain.models import Integration

@pytest.fixture
def mock_db():
    db = MagicMock()
    session = MagicMock()
    db.session.return_value.__enter__.return_value = session
    return db, session

@pytest.fixture
def mock_vault():
    return MagicMock()

@pytest.fixture
def repository(mock_db, mock_vault):
    db, _ = mock_db
    return IntegrationRepository(db=db, vault_client=mock_vault)

def test_get_all(repository, mock_db):
    db, session = mock_db
    schema = "schema-1"
    expected_integrations = [Integration(id="1", integration_type="type")]
    session.query.return_value.filter.return_value.all.return_value = expected_integrations

    result = repository.get_all(schema)

    assert result == expected_integrations
    db.session.assert_called_once_with(schema_name=schema)

def test_get_by_id_success(repository, mock_db):
    db, session = mock_db
    integration_id = "1"
    schema = "schema-1"
    expected_integration = Integration(id=integration_id, integration_type="type")
    session.query.return_value.filter.return_value.first.return_value = expected_integration

    result = repository.get_by_id(integration_id, schema)

    assert result == expected_integration

def test_get_by_id_not_found(repository, mock_db):
    db, session = mock_db
    session.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(IntegrationNotFoundError):
        repository.get_by_id("invalid", "schema")

def test_add(repository, mock_db, mock_vault):
    db, session = mock_db
    integration_type = "openai"
    api_endpoint = "http://api"
    api_key = "key"
    schema = "schema-1"

    result = repository.add(integration_type, api_endpoint, api_key, schema)

    assert result.integration_type == integration_type
    mock_vault.secrets.kv.v2.create_or_update_secret.assert_called_once()
    session.add.assert_called_once()
    session.commit.assert_called_once()

def test_delete_by_id_success(repository, mock_db):
    db, session = mock_db
    integration_id = "1"
    schema = "schema-1"
    entity = Integration(id=integration_id, is_active=True)
    session.query.return_value.filter.return_value.first.return_value = entity

    repository.delete_by_id(integration_id, schema)

    assert entity.is_active is False
    session.commit.assert_called_once()
