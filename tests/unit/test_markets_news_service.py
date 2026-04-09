import base64
import json
from unittest.mock import MagicMock

import pytest

from app.services.markets_news import MarketsNewsService


@pytest.fixture
def mock_es():
    return MagicMock()


@pytest.fixture
def service(mock_es):
    return MarketsNewsService(es=mock_es)


def _make_hit(doc_id, sort_value):
    return {
        "_id": doc_id,
        "_source": {
            "text_headline": f"Headline {doc_id}",
            "text_summary": f"Summary {doc_id}",
        },
        "sort": [sort_value],
    }


def _make_cursor(sort_value):
    return base64.urlsafe_b64encode(json.dumps([sort_value]).encode()).decode()


def _extract_template_params(mock_es):
    mock_es.search_template.assert_called_once()
    call_kwargs = mock_es.search_template.call_args
    return call_kwargs.kwargs["body"]["params"]


class TestGetNewsParams:
    def test_match_all_when_no_key_ticker_no_search_term(self, service, mock_es):
        mock_es.search_template.return_value = {"hits": {"hits": []}}

        service.get_news(index_name="test-index", size=5)

        params = _extract_template_params(mock_es)
        assert "key_ticker" not in params
        assert "search_term" not in params
        assert "id" not in params
        assert params["size"] == 5

    def test_key_ticker_included_when_provided(self, service, mock_es):
        mock_es.search_template.return_value = {"hits": {"hits": []}}

        service.get_news(index_name="test-index", key_ticker="AAPL")

        params = _extract_template_params(mock_es)
        assert params["key_ticker"] == "AAPL"
        assert "search_term" not in params

    def test_search_term_included_when_no_key_ticker(self, service, mock_es):
        mock_es.search_template.return_value = {"hits": {"hits": []}}

        service.get_news(index_name="test-index", search_term="Bezos")

        params = _extract_template_params(mock_es)
        assert "key_ticker" not in params
        assert params["search_term"] == "Bezos"

    def test_key_ticker_takes_precedence_over_search_term(self, service, mock_es):
        mock_es.search_template.return_value = {"hits": {"hits": []}}

        service.get_news(
            index_name="test-index", key_ticker="AAPL", search_term="Bezos"
        )

        params = _extract_template_params(mock_es)
        assert params["key_ticker"] == "AAPL"
        assert "search_term" not in params

    def test_id_included_when_provided(self, service, mock_es):
        mock_es.search_template.return_value = {"hits": {"hits": []}}

        service.get_news(index_name="test-index", id="doc-123")

        params = _extract_template_params(mock_es)
        assert params["id"] == "doc-123"

    def test_cursor_decoded_into_search_after(self, service, mock_es):
        mock_es.search_template.return_value = {"hits": {"hits": []}}
        cursor = _make_cursor(1704067200000)

        service.get_news(index_name="test-index", cursor=cursor)

        params = _extract_template_params(mock_es)
        assert params["search_after"] == [1704067200000]

    def test_no_search_after_when_cursor_is_none(self, service, mock_es):
        mock_es.search_template.return_value = {"hits": {"hits": []}}

        service.get_news(index_name="test-index")

        params = _extract_template_params(mock_es)
        assert "search_after" not in params

    def test_include_flags_passed_through(self, service, mock_es):
        mock_es.search_template.return_value = {"hits": {"hits": []}}

        service.get_news(
            index_name="test-index",
            include_text_content=True,
            include_key_ticker=True,
            include_obj_images=True,
        )

        params = _extract_template_params(mock_es)
        assert params["include_text_content"] is True
        assert params["include_key_ticker"] is True
        assert params["include_obj_images"] is True


class TestGetNewsResults:
    def test_returns_hits_and_cursor(self, service, mock_es):
        hit1 = _make_hit("1", 1704067200000)
        hit2 = _make_hit("2", 1704153600000)
        mock_es.search_template.return_value = {"hits": {"hits": [hit1, hit2]}}

        results, last_sort = service.get_news(index_name="test-index")

        assert len(results) == 2
        assert results[0]["_id"] == "1"
        assert results[1]["_id"] == "2"
        expected_cursor = base64.urlsafe_b64encode(
            json.dumps([1704153600000]).encode()
        ).decode()
        assert last_sort == expected_cursor

    def test_returns_none_cursor_when_no_hits(self, service, mock_es):
        mock_es.search_template.return_value = {"hits": {"hits": []}}

        results, last_sort = service.get_news(index_name="test-index")

        assert results == []
        assert last_sort is None
