import json
from unittest.mock import MagicMock

from app.services.agent_types.quaks.insights.tools import (
    build_get_markets_news_tool,
    build_get_insights_news_tool,
)


class TestBuildGetMarketsNewsTool:
    def test_returns_callable_tool(self):
        mock_service = MagicMock()
        mock_service.get_news.return_value = ([], None)
        tool = build_get_markets_news_tool(mock_service)
        assert tool.name == "get_markets_news"

    def test_invokes_service_and_returns_json(self):
        mock_service = MagicMock()
        mock_service.get_news.return_value = (
            [
                {
                    "_source": {
                        "text_headline": "Test Headline",
                        "text_summary": "Summary",
                        "text_content": "Content",
                        "key_source": "reuters",
                        "date_reference": "2025-01-10",
                        "key_ticker": ["AAPL"],
                    }
                }
            ],
            None,
        )
        tool = build_get_markets_news_tool(mock_service)
        result = tool.invoke({"search_term": "tech", "ticker": "AAPL", "days": 3, "size": 10})
        articles = json.loads(result)
        assert len(articles) == 1
        assert articles[0]["headline"] == "Test Headline"
        assert articles[0]["tickers"] == ["AAPL"]

    def test_caps_size_at_50(self):
        mock_service = MagicMock()
        mock_service.get_news.return_value = ([], None)
        tool = build_get_markets_news_tool(mock_service)
        tool.invoke({"search_term": "", "ticker": "", "days": 1, "size": 100})
        call_kwargs = mock_service.get_news.call_args[1]
        assert call_kwargs["size"] == 50

    def test_empty_search_and_ticker_pass_none(self):
        mock_service = MagicMock()
        mock_service.get_news.return_value = ([], None)
        tool = build_get_markets_news_tool(mock_service)
        tool.invoke({"search_term": "", "ticker": "", "days": 1, "size": 5})
        call_kwargs = mock_service.get_news.call_args[1]
        assert call_kwargs["search_term"] is None
        assert call_kwargs["key_ticker"] is None


class TestBuildGetInsightsNewsTool:
    def test_returns_callable_tool(self):
        mock_service = MagicMock()
        mock_service.get_insights_news.return_value = ([], None)
        tool = build_get_insights_news_tool(mock_service)
        assert tool.name == "get_insights_news"

    def test_invokes_service_and_returns_json(self):
        mock_service = MagicMock()
        mock_service.get_insights_news.return_value = (
            [
                {
                    "_source": {
                        "date_reference": "2025-01-10",
                        "text_executive_summary": "Market summary",
                        "text_report_html": "<p>Report</p>",
                    }
                }
            ],
            None,
        )
        tool = build_get_insights_news_tool(mock_service)
        result = tool.invoke({"date_from": "2025-01-01", "size": 5})
        briefings = json.loads(result)
        assert len(briefings) == 1
        assert briefings[0]["executive_summary"] == "Market summary"

    def test_caps_size_at_10(self):
        mock_service = MagicMock()
        mock_service.get_insights_news.return_value = ([], None)
        tool = build_get_insights_news_tool(mock_service)
        tool.invoke({"date_from": "", "size": 50})
        call_kwargs = mock_service.get_insights_news.call_args[1]
        assert call_kwargs["size"] == 10

    def test_empty_date_from_passes_none(self):
        mock_service = MagicMock()
        mock_service.get_insights_news.return_value = ([], None)
        tool = build_get_insights_news_tool(mock_service)
        tool.invoke({"date_from": "", "size": 5})
        call_kwargs = mock_service.get_insights_news.call_args[1]
        assert call_kwargs["date_from"] is None
