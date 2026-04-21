"""Tests for markets API endpoints."""
import pytest
from unittest.mock import MagicMock

from app.domain.exceptions.base import InvalidFieldError
from app.interface.api.markets.endpoints import (
    _validate_index_name,
    INDICATOR_CONFIG,
    SUPPORTED_INDICATORS,
    get_stats_close,
    get_company_profile,
    get_stats_close_bulk,
    get_market_caps_bulk,
    get_news,
    get_insights_news,
    get_published_content_preview,
    cancel_published_content,
    get_indicator,
)
from app.interface.api.markets.schema import (
    StatsCloseRequest,
    NewsListRequest,
    InsightsNewsListRequest,
    IndicatorRequest,
)


# The FastAPI endpoints are decorated with @inject which wraps them.
# Access the original function via __wrapped__ to call directly.
_get_stats_close = get_stats_close.__wrapped__
_get_company_profile = get_company_profile.__wrapped__
_get_stats_close_bulk = get_stats_close_bulk.__wrapped__
_get_market_caps_bulk = get_market_caps_bulk.__wrapped__
_get_news = get_news.__wrapped__
_get_insights_news = get_insights_news.__wrapped__
_get_published_content_preview = get_published_content_preview.__wrapped__
_cancel_published_content = cancel_published_content.__wrapped__
_get_indicator = get_indicator.__wrapped__


class TestValidateIndexName:
    def test_valid_names(self):
        _validate_index_name("stocks-eod")
        _validate_index_name("quaks_stocks-metadata_latest")
        _validate_index_name("abc123")

    def test_invalid_names(self):
        with pytest.raises(InvalidFieldError):
            _validate_index_name("UPPER_CASE")
        with pytest.raises(InvalidFieldError):
            _validate_index_name("has spaces")
        with pytest.raises(InvalidFieldError):
            _validate_index_name("has*wildcard")


class TestIndicatorConfig:
    def test_all_indicators_present(self):
        assert "ad" in INDICATOR_CONFIG
        assert "adx" in INDICATOR_CONFIG
        assert "cci" in INDICATOR_CONFIG
        assert "ema" in INDICATOR_CONFIG
        assert "macd" in INDICATOR_CONFIG
        assert "obv" in INDICATOR_CONFIG
        assert "rsi" in INDICATOR_CONFIG
        assert "stoch" in INDICATOR_CONFIG

    def test_supported_indicators_string(self):
        assert "ad" in SUPPORTED_INDICATORS
        assert "rsi" in SUPPORTED_INDICATORS


class TestGetStatsClose:
    @pytest.mark.asyncio
    async def test_returns_stats(self):
        mock_service = MagicMock()
        mock_service.get_stats_close.return_value = {
            "most_recent_close": 150.0,
            "most_recent_open": 148.0,
            "most_recent_high": 152.0,
            "most_recent_low": 147.0,
            "most_recent_volume": 1000000,
            "most_recent_date": "2025-01-10",
            "percent_variance": 1.5,
        }
        request = StatsCloseRequest(start_date="2025-01-01", end_date="2025-01-10")
        result = await _get_stats_close("stocks-eod", "AAPL", mock_service, request)
        assert result.key_ticker == "AAPL"
        assert result.most_recent_close == 150.0

    @pytest.mark.asyncio
    async def test_uses_default_dates(self):
        mock_service = MagicMock()
        mock_service.get_stats_close.return_value = {
            "most_recent_close": 150.0,
            "most_recent_open": 148.0,
            "most_recent_high": 152.0,
            "most_recent_low": 147.0,
            "most_recent_volume": 1000000,
            "most_recent_date": "2025-01-10",
            "percent_variance": 1.0,
        }
        request = StatsCloseRequest()
        result = await _get_stats_close("stocks-eod", "AAPL", mock_service, request)
        assert result.key_ticker == "AAPL"
        # Verify default dates were passed (start_date ~90 days ago, end_date ~today)
        call_kwargs = mock_service.get_stats_close.call_args[1]
        assert call_kwargs["start_date"] is not None
        assert call_kwargs["end_date"] is not None


class TestGetCompanyProfile:
    @pytest.mark.asyncio
    async def test_returns_profile(self):
        mock_service = MagicMock()
        mock_service.get_company_profile.return_value = {
            "key_ticker": "AAPL",
            "name": "Apple Inc",
            "exchange": "NASDAQ",
            "sector": "Technology",
        }
        result = await _get_company_profile("stocks-metadata", "AAPL", mock_service)
        assert result.key_ticker == "AAPL"


class TestGetStatsCloseBulk:
    @pytest.mark.asyncio
    async def test_returns_bulk_stats(self):
        mock_service = MagicMock()
        mock_service.get_stats_close_bulk.return_value = [
            {
                "key_ticker": "AAPL",
                "most_recent_close": 150.0,
                "most_recent_open": 148.0,
                "most_recent_high": 152.0,
                "most_recent_low": 147.0,
                "most_recent_volume": 1000000,
                "most_recent_date": "2025-01-10",
                "percent_variance": 1.5,
            },
            {
                "key_ticker": "MSFT",
                "most_recent_close": 400.0,
                "most_recent_open": 398.0,
                "most_recent_high": 402.0,
                "most_recent_low": 397.0,
                "most_recent_volume": 500000,
                "most_recent_date": "2025-01-10",
                "percent_variance": 0.5,
            },
        ]
        result = await _get_stats_close_bulk("stocks-eod", "AAPL,MSFT", mock_service)
        assert len(result.items) == 2
        assert result.items[0].key_ticker == "AAPL"
        assert result.items[1].key_ticker == "MSFT"


class TestGetMarketCapsBulk:
    @pytest.mark.asyncio
    async def test_returns_market_caps(self):
        mock_service = MagicMock()
        mock_service.get_market_caps_bulk.return_value = [
            {"key_ticker": "AAPL", "market_capitalization": 3000000000000},
        ]
        result = await _get_market_caps_bulk("stocks-metadata", "AAPL", mock_service)
        assert len(result.items) == 1
        assert result.items[0].market_capitalization == 3000000000000


class TestGetNews:
    @pytest.mark.asyncio
    async def test_returns_news(self):
        mock_service = MagicMock()
        mock_service.get_news.return_value = (
            [
                {
                    "_id": "abc123",
                    "_source": {
                        "key_source": "reuters",
                        "text_headline": "Tech Rally",
                        "text_summary": "Stocks up",
                        "text_content": "Full content",
                        "date_reference": "2025-01-10",
                        "obj_images": None,
                        "key_ticker": ["AAPL"],
                    },
                }
            ],
            "cursor123",
        )
        request = NewsListRequest(size=5)
        result = await _get_news("markets-news", mock_service, request)
        assert len(result.items) == 1
        assert result.items[0].headline == "Tech Rally"
        assert result.cursor == "cursor123"


class TestGetInsightsNews:
    @pytest.mark.asyncio
    async def test_returns_insights(self):
        mock_service = MagicMock()
        mock_service.get_insights_news.return_value = (
            [
                {
                    "_id": "ins1",
                    "_source": {
                        "date_reference": "2025-01-10",
                        "text_executive_summary": "Market summary",
                        "text_report_html": "<p>Report</p>",
                        "key_skill_name": "/news_analyst",
                        "key_author_username": "agent",
                        "key_language_model_name": "claude-opus-4-7",
                    },
                }
            ],
            None,
        )
        request = InsightsNewsListRequest(size=5, include_report_html=True)
        result = await _get_insights_news("insights-news", mock_service, request)
        assert len(result.items) == 1
        assert result.items[0].executive_summary == "Market summary"
        assert result.items[0].language_model_name == "claude-opus-4-7"


class TestGetPublishedContentPreview:
    @pytest.mark.asyncio
    async def test_pending_status(self):
        mock_service = MagicMock()
        mock_service.get_by_id.return_value = {
            "flag_cancelled": False,
            "flag_processed": False,
            "text_executive_summary": "Summary",
            "text_report_html": "<p>Report</p>",
            "key_skill_name": "/news",
            "key_author_username": "user",
            "date_timestamp": "2025-01-10",
        }
        result = await _get_published_content_preview("doc1", mock_service)
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_processed_status(self):
        mock_service = MagicMock()
        mock_service.get_by_id.return_value = {
            "flag_cancelled": False,
            "flag_processed": True,
            "text_executive_summary": "S",
            "text_report_html": "",
            "key_skill_name": "",
            "key_author_username": "",
            "date_timestamp": "",
        }
        result = await _get_published_content_preview("doc1", mock_service)
        assert result.status == "processed"

    @pytest.mark.asyncio
    async def test_cancelled_status(self):
        mock_service = MagicMock()
        mock_service.get_by_id.return_value = {
            "flag_cancelled": True,
            "flag_processed": False,
            "text_executive_summary": "S",
            "text_report_html": "",
            "key_skill_name": "",
            "key_author_username": "",
            "date_timestamp": "",
        }
        result = await _get_published_content_preview("doc1", mock_service)
        assert result.status == "cancelled"


class TestCancelPublishedContent:
    @pytest.mark.asyncio
    async def test_cancels(self):
        mock_service = MagicMock()
        result = await _cancel_published_content("doc1", mock_service)
        assert result.status == "cancelled"
        assert result.doc_id == "doc1"
        mock_service.cancel_publishing.assert_called_once_with("doc1")


class TestGetIndicator:
    @pytest.mark.asyncio
    async def test_returns_indicator_data(self):
        mock_service = MagicMock()
        mock_service.get_indicator_rsi.return_value = [
            {"date": "2025-01-10", "value": 62.5}
        ]
        request = IndicatorRequest(
            start_date="2025-01-01",
            end_date="2025-01-10",
            period=14,
        )
        result = await _get_indicator("rsi", "stocks-eod", "AAPL", mock_service, request)
        assert result.indicator == "rsi"
        assert result.key_ticker == "AAPL"
        assert len(result.data) == 1

    @pytest.mark.asyncio
    async def test_invalid_indicator_name(self):
        mock_service = MagicMock()
        request = IndicatorRequest()
        with pytest.raises(InvalidFieldError):
            await _get_indicator("xyz", "stocks-eod", "AAPL", mock_service, request)

    @pytest.mark.asyncio
    async def test_uses_default_dates(self):
        mock_service = MagicMock()
        mock_service.get_indicator_ad.return_value = []
        request = IndicatorRequest()
        result = await _get_indicator("ad", "stocks-eod", "AAPL", mock_service, request)
        assert result.indicator == "ad"

    @pytest.mark.asyncio
    async def test_ema_indicator(self):
        mock_service = MagicMock()
        mock_service.get_indicator_ema.return_value = []
        request = IndicatorRequest(short_window=12, long_window=26)
        result = await _get_indicator("ema", "stocks-eod", "AAPL", mock_service, request)
        assert result.indicator == "ema"

    @pytest.mark.asyncio
    async def test_macd_indicator(self):
        mock_service = MagicMock()
        mock_service.get_indicator_macd.return_value = []
        request = IndicatorRequest(short_window=12, long_window=26, signal_window=9)
        result = await _get_indicator("macd", "stocks-eod", "AAPL", mock_service, request)
        assert result.indicator == "macd"

    @pytest.mark.asyncio
    async def test_stoch_indicator(self):
        mock_service = MagicMock()
        mock_service.get_indicator_stoch.return_value = []
        request = IndicatorRequest(lookback=14, smooth_k=3, smooth_d=3)
        result = await _get_indicator("stoch", "stocks-eod", "AAPL", mock_service, request)
        assert result.indicator == "stoch"
