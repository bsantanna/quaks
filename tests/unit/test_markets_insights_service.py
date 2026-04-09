from unittest.mock import MagicMock
import pytest
import base64
import json
from app.services.markets_insights import MarketsInsightsService

@pytest.fixture
def mock_es():
    return MagicMock()

@pytest.fixture
def service(mock_es):
    return MarketsInsightsService(es=mock_es)

def test_get_insights_news(service, mock_es):
    mock_es.search_template.return_value = {
        'hits': {
            'hits': [
                {'_id': '1', 'sort': [123], '_source': {}}
            ]
        }
    }
    
    results, last_sort = service.get_insights_news("index")
    
    assert len(results) == 1
    assert last_sort is not None
    mock_es.search_template.assert_called_once()

def test_get_insights_news_with_cursor(service, mock_es):
    cursor = base64.urlsafe_b64encode(json.dumps([123]).encode()).decode()
    mock_es.search_template.return_value = {'hits': {'hits': []}}
    
    service.get_insights_news("index", cursor=cursor)
    
    # Check if search_after was passed in params
    args = mock_es.search_template.call_args
    assert args[1]['body']['params']['search_after'] == [123]
