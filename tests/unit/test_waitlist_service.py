from unittest.mock import MagicMock
import pytest
from elasticsearch import ConflictError
from app.services.waitlist import WaitlistService
from app.domain.exceptions.base import DuplicateEntryError

@pytest.fixture
def mock_es():
    return MagicMock()

@pytest.fixture
def service(mock_es):
    return WaitlistService(es=mock_es)

def test_register_success(service, mock_es):
    mock_es.indices.exists_alias.return_value = False
    
    service.register("test@test.com", "user1", "First", "Last")
    
    mock_es.index.assert_called_once()
    mock_es.indices.put_alias.assert_called_once()

def test_register_conflict(service, mock_es):
    mock_es.index.side_effect = ConflictError("conflict", MagicMock(), MagicMock())
    
    with pytest.raises(DuplicateEntryError):
        service.register("test@test.com", "user1", "First", "Last")
