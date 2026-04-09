from unittest.mock import MagicMock
import pytest
from elasticsearch import ConflictError, NotFoundError as ESNotFoundError
from app.services.published_content import PublishedContentService
from app.domain.exceptions.base import DuplicateEntryError, PublishedContentNotFoundError

@pytest.fixture
def mock_es():
    return MagicMock()

@pytest.fixture
def service(mock_es):
    return PublishedContentService(es=mock_es)

def test_publish_success(service, mock_es):
    mock_es.indices.exists_alias.return_value = False
    
    doc_id = service.publish("summary", "html", "skill", "author")
    
    assert doc_id is not None
    mock_es.index.assert_called_once()
    mock_es.indices.update_aliases.assert_called_once()

def test_get_by_id_success(service, mock_es):
    mock_es.get.return_value = {"_source": {"content": "data"}}
    
    result = service.get_by_id("id1")
    assert result == {"content": "data"}

def test_get_by_id_not_found(service, mock_es):
    mock_es.get.side_effect = ESNotFoundError("not found", MagicMock(), MagicMock())
    
    with pytest.raises(PublishedContentNotFoundError):
        service.get_by_id("id1")

def test_cancel_publishing_success(service, mock_es):
    mock_es.get.return_value = {"_index": "index1"}
    
    service.cancel_publishing("id1")
    
    mock_es.update.assert_called_once()
    assert mock_es.update.call_args[1]["doc"] == {"flag_cancelled": True}
