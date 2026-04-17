from unittest.mock import MagicMock

import pytest

from app.services.markets_stats import MarketsStatsService


@pytest.fixture
def mock_es():
    return MagicMock()


@pytest.fixture
def service(mock_es):
    return MarketsStatsService(es=mock_es)


def _extract_template_params(mock_es):
    mock_es.search_template.assert_called_once()
    call_kwargs = mock_es.search_template.call_args
    return call_kwargs.kwargs["body"]["params"]


def _make_bucket(ticker, stats):
    return {"key": ticker, "recent_stats": {"value": stats}}


def _make_stats(close=150.0, open_=148.0, high=152.0, low=147.0, volume=1000000.0, date="2026-03-05", variance=1.35):
    return {
        "most_recent_close": close,
        "most_recent_open": open_,
        "most_recent_high": high,
        "most_recent_low": low,
        "most_recent_volume": volume,
        "most_recent_date": date,
        "percent_variance": variance,
    }


class TestGetStatsClose:
    def test_calls_template_with_correct_params(self, service, mock_es):
        mock_es.search_template.return_value = {
            "aggregations": {"recent_stats": {"value": _make_stats()}}
        }

        service.get_stats_close(
            index_name="stocks-eod",
            key_ticker="AAPL",
            start_date="2026-01-01",
            end_date="2026-03-05",
        )

        params = _extract_template_params(mock_es)
        assert params["key_ticker"] == "AAPL"
        assert params["date_gte"] == "2026-01-01"
        assert params["date_lte"] == "2026-03-05"

    def test_returns_stats_value(self, service, mock_es):
        expected = _make_stats()
        mock_es.search_template.return_value = {
            "aggregations": {"recent_stats": {"value": expected}}
        }

        result = service.get_stats_close(
            index_name="stocks-eod",
            key_ticker="AAPL",
            start_date="2026-01-01",
            end_date="2026-03-05",
        )

        assert result == expected


class TestGetStatsCloseBulk:
    def test_calls_template_with_correct_params(self, service, mock_es):
        mock_es.search_template.return_value = {
            "aggregations": {"by_ticker": {"buckets": []}}
        }

        service.get_stats_close_bulk(
            index_name="stocks-eod",
            key_tickers=["AAPL", "MSFT"],
            start_date="2026-02-27",
            end_date="2026-03-06",
        )

        params = _extract_template_params(mock_es)
        assert params["key_tickers"] == ["AAPL", "MSFT"]
        assert params["date_gte"] == "2026-02-27"
        assert params["date_lte"] == "2026-03-06"
        assert params["size"] == 2

    def test_returns_results_with_ticker_key(self, service, mock_es):
        mock_es.search_template.return_value = {
            "aggregations": {
                "by_ticker": {
                    "buckets": [
                        _make_bucket("AAPL", _make_stats(close=150.0, variance=1.35)),
                        _make_bucket("MSFT", _make_stats(close=400.0, variance=-0.5)),
                    ]
                }
            }
        }

        results = service.get_stats_close_bulk(
            index_name="stocks-eod",
            key_tickers=["AAPL", "MSFT"],
            start_date="2026-02-27",
            end_date="2026-03-06",
        )

        assert len(results) == 2
        assert results[0]["key_ticker"] == "AAPL"
        assert results[0]["most_recent_close"] == 150.0
        assert results[0]["percent_variance"] == 1.35
        assert results[1]["key_ticker"] == "MSFT"
        assert results[1]["percent_variance"] == -0.5

    def test_skips_buckets_with_null_stats(self, service, mock_es):
        mock_es.search_template.return_value = {
            "aggregations": {
                "by_ticker": {
                    "buckets": [
                        _make_bucket("AAPL", _make_stats()),
                        _make_bucket("BADTICKER", None),
                    ]
                }
            }
        }

        results = service.get_stats_close_bulk(
            index_name="stocks-eod",
            key_tickers=["AAPL", "BADTICKER"],
            start_date="2026-02-27",
            end_date="2026-03-06",
        )

        assert len(results) == 1
        assert results[0]["key_ticker"] == "AAPL"

    def test_empty_tickers_returns_empty(self, service, mock_es):
        mock_es.search_template.return_value = {
            "aggregations": {"by_ticker": {"buckets": []}}
        }

        results = service.get_stats_close_bulk(
            index_name="stocks-eod",
            key_tickers=[],
            start_date="2026-02-27",
            end_date="2026-03-06",
        )

        assert results == []

    def test_queries_correct_index(self, service, mock_es):
        mock_es.search_template.return_value = {
            "aggregations": {"by_ticker": {"buckets": []}}
        }

        service.get_stats_close_bulk(
            index_name="stocks-eod",
            key_tickers=["AAPL"],
            start_date="2026-02-27",
            end_date="2026-03-06",
        )

        call_kwargs = mock_es.search_template.call_args
        assert call_kwargs.kwargs["index"] == "stocks-eod"


def _make_market_cap_bucket(ticker, market_cap):
    return {
        "key": ticker,
        "latest": {
            "hits": {
                "hits": [{"_source": {"market_capitalization": market_cap}}] if market_cap is not None else []
            }
        }
    }


class TestGetMarketCapsBulk:
    def test_calls_template_with_correct_params(self, service, mock_es):
        mock_es.search_template.return_value = {
            "aggregations": {"by_ticker": {"buckets": []}}
        }

        service.get_market_caps_bulk(
            index_name="quaks_stocks-metadata_latest",
            key_tickers=["AAPL", "MSFT"],
        )

        params = _extract_template_params(mock_es)
        assert params["key_tickers"] == ["AAPL", "MSFT"]
        assert params["size"] == 2

    def test_returns_market_caps(self, service, mock_es):
        mock_es.search_template.return_value = {
            "aggregations": {
                "by_ticker": {
                    "buckets": [
                        _make_market_cap_bucket("AAPL", 3000000000000),
                        _make_market_cap_bucket("MSFT", 2800000000000),
                    ]
                }
            }
        }

        results = service.get_market_caps_bulk(
            index_name="quaks_stocks-metadata_latest",
            key_tickers=["AAPL", "MSFT"],
        )

        assert len(results) == 2
        assert results[0]["key_ticker"] == "AAPL"
        assert results[0]["market_capitalization"] == 3000000000000
        assert results[1]["key_ticker"] == "MSFT"
        assert results[1]["market_capitalization"] == 2800000000000

    def test_skips_tickers_with_no_hits(self, service, mock_es):
        mock_es.search_template.return_value = {
            "aggregations": {
                "by_ticker": {
                    "buckets": [
                        _make_market_cap_bucket("AAPL", 3000000000000),
                        _make_market_cap_bucket("UNKNOWN", None),
                    ]
                }
            }
        }

        results = service.get_market_caps_bulk(
            index_name="quaks_stocks-metadata_latest",
            key_tickers=["AAPL", "UNKNOWN"],
        )

        assert len(results) == 1
        assert results[0]["key_ticker"] == "AAPL"

    def test_empty_tickers_returns_empty(self, service, mock_es):
        mock_es.search_template.return_value = {
            "aggregations": {"by_ticker": {"buckets": []}}
        }

        results = service.get_market_caps_bulk(
            index_name="quaks_stocks-metadata_latest",
            key_tickers=[],
        )

        assert results == []


class TestGetCompanyProfile:
    def test_returns_profile(self, service, mock_es):
        mock_es.search_template.return_value = {
            "hits": {"hits": [{"_source": {"key_ticker": "AAPL", "name": "Apple Inc"}}]}
        }
        result = service.get_company_profile("stocks-metadata", "AAPL")
        assert result["key_ticker"] == "AAPL"
        assert result["name"] == "Apple Inc"

    def test_returns_empty_when_no_hits(self, service, mock_es):
        mock_es.search_template.return_value = {"hits": {"hits": []}}
        result = service.get_company_profile("stocks-metadata", "UNKNOWN")
        assert result == {}


class TestIndicators:
    def _mock_indicator_response(self, mock_es, agg_key, value):
        mock_es.search_template.return_value = {
            "aggregations": {agg_key: {"value": value}}
        }

    def test_get_indicator_ad(self, service, mock_es):
        self._mock_indicator_response(mock_es, "ad_stats", [{"date": "2025-01-10", "ad": 100}])
        result = service.get_indicator_ad("stocks-eod", "AAPL", "2025-01-01", "2025-01-10")
        assert result == [{"date": "2025-01-10", "ad": 100}]

    def test_get_indicator_adx(self, service, mock_es):
        self._mock_indicator_response(mock_es, "adx_stats", [{"date": "2025-01-10", "adx": 25}])
        result = service.get_indicator_adx("stocks-eod", "AAPL", "2025-01-01", "2025-01-10", 14)
        assert result == [{"date": "2025-01-10", "adx": 25}]

    def test_get_indicator_cci(self, service, mock_es):
        self._mock_indicator_response(mock_es, "cci_stats", [{"date": "2025-01-10", "cci": 50}])
        result = service.get_indicator_cci("stocks-eod", "AAPL", "2025-01-01", "2025-01-10", 20, 0.015)
        assert result == [{"date": "2025-01-10", "cci": 50}]

    def test_get_indicator_ema(self, service, mock_es):
        self._mock_indicator_response(mock_es, "ema_stats", [{"date": "2025-01-10", "ema": 150}])
        result = service.get_indicator_ema("stocks-eod", "AAPL", "2025-01-01", "2025-01-10", 12, 26)
        assert result == [{"date": "2025-01-10", "ema": 150}]

    def test_get_indicator_macd(self, service, mock_es):
        self._mock_indicator_response(mock_es, "macd_stats", [{"date": "2025-01-10", "macd": 1.5}])
        result = service.get_indicator_macd("stocks-eod", "AAPL", "2025-01-01", "2025-01-10", 12, 26, 9)
        assert result == [{"date": "2025-01-10", "macd": 1.5}]

    def test_get_indicator_obv(self, service, mock_es):
        self._mock_indicator_response(mock_es, "obv_stats", [{"date": "2025-01-10", "obv": 500000}])
        result = service.get_indicator_obv("stocks-eod", "AAPL", "2025-01-01", "2025-01-10")
        assert result == [{"date": "2025-01-10", "obv": 500000}]

    def test_get_indicator_rsi(self, service, mock_es):
        self._mock_indicator_response(mock_es, "rsi_stats", [{"date": "2025-01-10", "rsi": 62.35}])
        result = service.get_indicator_rsi("stocks-eod", "AAPL", "2025-01-01", "2025-01-10", 14)
        assert result == [{"date": "2025-01-10", "rsi": 62.35}]

    def test_get_indicator_stoch(self, service, mock_es):
        self._mock_indicator_response(mock_es, "stoch_stats", [{"date": "2025-01-10", "stoch_k": 75}])
        result = service.get_indicator_stoch("stocks-eod", "AAPL", "2025-01-01", "2025-01-10", 14, 3, 3)
        assert result == [{"date": "2025-01-10", "stoch_k": 75}]
