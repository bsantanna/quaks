import pytest

from app.domain.exceptions.base import InvalidFieldError
from app.interface.api.markets.schema import (
    NewsListRequest,
    InsightsNewsListRequest,
    StatsCloseBulkRequest,
    StatsCloseRequest,
    IndicatorRequest,
    _validate_date_format,
    _validate_date_order,
    CompanyProfile,
    StatsClose,
    StatsCloseBulkResponse,
    MarketCapItem,
    MarketCapsBulkRequest,
    MarketCapsBulkResponse,
    IndicatorResponse,
    NewsItem,
    NewsList,
    InsightsNewsItem,
    InsightsNewsList,
    PublishedContentPreview,
    CancelPublishingResponse,
    _DateRangeRequest,
)


class TestValidateDateFormat:
    def test_valid_date(self):
        assert _validate_date_format("2025-01-15") == "2025-01-15"

    def test_none_passes_through(self):
        assert _validate_date_format(None) is None

    def test_invalid_date_raises(self):
        with pytest.raises(InvalidFieldError):
            _validate_date_format("not-a-date")

    def test_wrong_format_raises(self):
        with pytest.raises(InvalidFieldError):
            _validate_date_format("01/15/2025")


class TestValidateDateOrder:
    def test_valid_order(self):
        _validate_date_order("2025-01-01", "2025-01-15")

    def test_none_dates_pass(self):
        _validate_date_order(None, None)
        _validate_date_order("2025-01-01", None)
        _validate_date_order(None, "2025-01-15")

    def test_same_date_raises(self):
        with pytest.raises(InvalidFieldError):
            _validate_date_order("2025-01-15", "2025-01-15")

    def test_reversed_order_raises(self):
        with pytest.raises(InvalidFieldError):
            _validate_date_order("2025-06-01", "2025-01-01")


class TestNewsListRequest:
    def test_empty_string_becomes_none(self):
        req = NewsListRequest(size=5, id="", key_ticker="", search_term="", cursor="")
        assert req.id is None
        assert req.key_ticker is None
        assert req.search_term is None
        assert req.cursor is None

    def test_valid_date_fields(self):
        req = NewsListRequest(size=5, date_from="2025-01-01", date_to="2025-06-01")
        assert req.date_from == "2025-01-01"
        assert req.date_to == "2025-06-01"

    def test_invalid_date_raises(self):
        with pytest.raises(Exception):
            NewsListRequest(size=5, date_from="bad-date")


class TestInsightsNewsListRequest:
    def test_empty_string_becomes_none(self):
        req = InsightsNewsListRequest(size=5, id="", cursor="")
        assert req.id is None
        assert req.cursor is None

    def test_valid_dates(self):
        req = InsightsNewsListRequest(size=5, date_from="2025-01-01", date_to="2025-06-01")
        assert req.date_from == "2025-01-01"


class TestStatsCloseBulkRequest:
    def test_valid_construction(self):
        req = StatsCloseBulkRequest(key_tickers=["AAPL", "MSFT"], start_date="2025-01-01", end_date="2025-06-01")
        assert req.key_tickers == ["AAPL", "MSFT"]

    def test_invalid_date_order_raises(self):
        with pytest.raises(Exception):
            StatsCloseBulkRequest(key_tickers=["AAPL"], start_date="2025-06-01", end_date="2025-01-01")


class TestStatsCloseRequest:
    def test_valid_construction(self):
        req = StatsCloseRequest(start_date="2025-01-01", end_date="2025-06-01")
        assert req.start_date == "2025-01-01"

    def test_invalid_order_raises(self):
        with pytest.raises(Exception):
            StatsCloseRequest(start_date="2025-06-01", end_date="2025-01-01")


class TestIndicatorRequest:
    def test_valid_with_all_params(self):
        req = IndicatorRequest(
            start_date="2025-01-01",
            end_date="2025-06-01",
            period=14,
            constant=0.015,
            short_window=12,
            long_window=26,
            signal_window=9,
            lookback=14,
            smooth_k=3,
            smooth_d=3,
        )
        assert req.period == 14

    def test_invalid_date_order_raises(self):
        with pytest.raises(Exception):
            IndicatorRequest(start_date="2025-06-01", end_date="2025-01-01")


class TestDateRangeRequest:
    def test_valid_range(self):
        req = _DateRangeRequest(start_date="2025-01-01", end_date="2025-06-01")
        assert req.start_date == "2025-01-01"

    def test_invalid_order_raises(self):
        with pytest.raises(Exception):
            _DateRangeRequest(start_date="2025-06-01", end_date="2025-01-01")

    def test_none_raises(self):
        with pytest.raises(Exception):
            _DateRangeRequest(start_date=None, end_date="2025-06-01")


class TestResponseModels:
    def test_stats_close(self):
        sc = StatsClose(key_ticker="AAPL", most_recent_close=150.0, most_recent_open=148.0,
                        most_recent_high=152.0, most_recent_low=147.0, most_recent_volume=1000000.0,
                        most_recent_date="2025-01-10", percent_variance=1.23)
        assert sc.key_ticker == "AAPL"

    def test_stats_close_bulk_response(self):
        resp = StatsCloseBulkResponse(items=[])
        assert resp.items == []

    def test_market_cap_item(self):
        item = MarketCapItem(key_ticker="AAPL", market_capitalization=3000000000000)
        assert item.key_ticker == "AAPL"

    def test_market_caps_bulk_request(self):
        req = MarketCapsBulkRequest(key_tickers=["AAPL"])
        assert req.key_tickers == ["AAPL"]

    def test_market_caps_bulk_response(self):
        resp = MarketCapsBulkResponse(items=[])
        assert resp.items == []

    def test_indicator_response(self):
        resp = IndicatorResponse(key_ticker="AAPL", indicator="rsi", data=[{"date": "2025-01-10", "value": 62.35}])
        assert resp.indicator == "rsi"

    def test_news_item(self):
        item = NewsItem(id="1", date="2025-01-10", source="reuters", headline="Test", summary="Summary", content=None, images=None, key_ticker=None)
        assert item.id == "1"

    def test_news_list(self):
        nl = NewsList(items=[], cursor=None)
        assert nl.items == []

    def test_insights_news_item(self):
        item = InsightsNewsItem(id="1", date="2025-01-10", executive_summary="Summary", report_html=None)
        assert item.id == "1"

    def test_insights_news_list(self):
        inl = InsightsNewsList(items=[], cursor=None)
        assert inl.items == []

    def test_company_profile(self):
        cp = CompanyProfile(key_ticker="AAPL", name="Apple Inc")
        assert cp.key_ticker == "AAPL"

    def test_published_content_preview(self):
        pcp = PublishedContentPreview(doc_id="d1", status="pending", executive_summary="s", report_html="<p>r</p>", skill_name="news", author_username="user", date_timestamp="2025-01-10")
        assert pcp.doc_id == "d1"

    def test_cancel_publishing_response(self):
        cpr = CancelPublishingResponse(doc_id="d1", status="cancelled")
        assert cpr.status == "cancelled"
