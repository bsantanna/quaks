"""Tests for format_bulk_* functions and post_to_x in data_ingestion_utils."""
import json
from unittest.mock import MagicMock, patch

import pandas as pd

from app.utils.data_ingestion_utils import (
    format_bulk_stocks_insider_trades,
    format_bulk_stocks_metadata,
    format_bulk_stocks_fundamental_income_statement,
    format_bulk_stocks_fundamental_balance_sheet,
    format_bulk_stocks_fundamental_cash_flow,
    format_bulk_stocks_fundamental_earnings_estimates,
    format_bulk_markets_news,
    post_to_x,
    _enrich_metadata_with_metrics,
    _finnhub_get,
    _es_bulk_post,
)


class TestFormatBulkStocksInsiderTrades:
    def test_formats_trades(self):
        data = [
            {
                "name": "John Doe",
                "transactionDate": "2025-01-10",
                "transactionCode": "P",
                "transactionPrice": 150.0,
                "change": 1000,
            },
            {
                "name": "Jane Smith",
                "transactionDate": "2025-01-11",
                "transactionCode": "S",
                "transactionPrice": 155.0,
                "change": -500,
            },
        ]
        result = format_bulk_stocks_insider_trades("AAPL", data, "latest")
        decoded = result.decode("utf-8")
        assert "quaks_stocks-insider-trades_latest" in decoded
        assert "AAPL" in decoded
        assert "Acquisition" in decoded
        assert "Disposal" in decoded

    def test_skips_missing_transaction_date(self):
        data = [{"name": "No Date", "transactionDate": None, "transactionCode": "P"}]
        result = format_bulk_stocks_insider_trades("AAPL", data, "latest")
        assert result == b""

    def test_empty_data(self):
        result = format_bulk_stocks_insider_trades("AAPL", [], "latest")
        assert result == b""

    def test_unknown_transaction_code(self):
        data = [
            {
                "name": "Unknown",
                "transactionDate": "2025-01-10",
                "transactionCode": "X",
                "transactionPrice": 100.0,
                "change": 50,
            }
        ]
        result = format_bulk_stocks_insider_trades("AAPL", data, "latest")
        assert b"Unknown" in result

    def test_grant_award_code(self):
        data = [
            {
                "name": "Award Person",
                "transactionDate": "2025-01-10",
                "transactionCode": "A",
                "transactionPrice": None,
                "change": 200,
            }
        ]
        result = format_bulk_stocks_insider_trades("AAPL", data, "latest")
        assert b"Acquisition" in result


class TestFormatBulkStocksMetadata:
    def test_formats_metadata(self):
        profile = {
            "ticker": "AAPL",
            "name": "Apple Inc",
            "exchange": "NASDAQ",
            "currency": "USD",
            "country": "US",
            "finnhubIndustry": "Technology",
            "weburl": "https://apple.com",
            "marketCapitalization": 3000000.0,  # millions
            "shareOutstanding": 15000.0,  # millions
        }
        result = format_bulk_stocks_metadata("AAPL", profile, "latest")
        decoded = result.decode("utf-8")
        assert "quaks_stocks-metadata_latest" in decoded
        assert "AAPL" in decoded
        lines = decoded.strip().split("\n")
        doc = json.loads(lines[1])
        assert doc["market_capitalization"] == 3000000000000
        assert doc["shares_outstanding"] == 15000000000

    def test_handles_missing_market_cap(self):
        profile = {"ticker": "AAPL", "name": "Apple"}
        result = format_bulk_stocks_metadata("AAPL", profile, "latest")
        lines = result.decode("utf-8").strip().split("\n")
        doc = json.loads(lines[1])
        assert doc["market_capitalization"] is None
        assert doc["shares_outstanding"] is None


class TestEnrichMetadataWithMetrics:
    @patch("app.utils.data_ingestion_utils._finnhub_get")
    def test_enriches_with_metrics(self, mock_get):
        mock_get.return_value = {
            "metric": {
                "peBasicExclExtraTTM": 30.5,
                "beta": 1.2,
                "52WeekHigh": 200.0,
                "52WeekLow": 130.0,
                "revenuePerShareTTM": 25.0,
            }
        }
        doc = {}
        result = _enrich_metadata_with_metrics("AAPL", doc)
        assert result["pe_ratio"] == 30.5
        assert result["beta"] == 1.2
        assert result["week_52_high"] == 200.0
        assert result["week_52_low"] == 130.0

    @patch("app.utils.data_ingestion_utils._finnhub_get")
    def test_handles_empty_metrics(self, mock_get):
        mock_get.return_value = {"metric": {}}
        doc = {"pe_ratio": None}
        result = _enrich_metadata_with_metrics("AAPL", doc)
        assert result["pe_ratio"] is None


class TestFormatBulkStocksFundamentalIncomeStatement:
    def test_formats_income_statement(self):
        reports = [
            {
                "endDate": "2025-03-31",
                "report": {
                    "ic": [
                        {"concept": "Revenues", "label": "Revenue", "value": 100000000},
                        {"concept": "NetIncomeLoss", "label": "Net Income", "value": 20000000},
                        {"concept": "GrossProfit", "label": "Gross Profit", "value": 50000000},
                    ]
                },
            }
        ]
        result = format_bulk_stocks_fundamental_income_statement("AAPL", reports, "latest")
        decoded = result.decode("utf-8")
        assert "quaks_stocks-fundamental-income-statement_latest" in decoded
        lines = decoded.strip().split("\n")
        doc = json.loads(lines[1])
        assert doc["total_revenue"] == 100000000
        assert doc["net_income"] == 20000000
        assert doc["gross_profit"] == 50000000

    def test_skips_report_without_end_date(self):
        reports = [{"endDate": "", "report": {"ic": [{"concept": "Revenues", "value": 100}]}}]
        result = format_bulk_stocks_fundamental_income_statement("AAPL", reports, "latest")
        assert result == b""

    def test_skips_report_without_ic(self):
        reports = [{"endDate": "2025-03-31", "report": {"ic": []}}]
        result = format_bulk_stocks_fundamental_income_statement("AAPL", reports, "latest")
        assert result == b""

    def test_empty_reports(self):
        result = format_bulk_stocks_fundamental_income_statement("AAPL", [], "latest")
        assert result == b""

    def test_end_date_with_time(self):
        reports = [
            {
                "endDate": "2025-03-31 00:00:00",
                "report": {
                    "ic": [{"concept": "Revenues", "label": "Revenue", "value": 100}]
                },
            }
        ]
        result = format_bulk_stocks_fundamental_income_statement("AAPL", reports, "latest")
        assert b"2025-03-31" in result


class TestFormatBulkStocksFundamentalBalanceSheet:
    def test_formats_balance_sheet(self):
        reports = [
            {
                "endDate": "2025-03-31",
                "report": {
                    "bs": [
                        {"concept": "Assets", "label": "Total Assets", "value": 500000000},
                        {"concept": "Liabilities", "label": "Total Liabilities", "value": 200000000},
                        {"concept": "StockholdersEquity", "label": "Equity", "value": 300000000},
                    ]
                },
            }
        ]
        result = format_bulk_stocks_fundamental_balance_sheet("AAPL", reports, "latest")
        decoded = result.decode("utf-8")
        assert "quaks_stocks-fundamental-balance-sheet_latest" in decoded
        lines = decoded.strip().split("\n")
        doc = json.loads(lines[1])
        assert doc["total_assets"] == 500000000
        assert doc["total_liabilities"] == 200000000
        assert doc["total_shareholder_equity"] == 300000000

    def test_skips_report_without_bs(self):
        reports = [{"endDate": "2025-03-31", "report": {"bs": []}}]
        result = format_bulk_stocks_fundamental_balance_sheet("AAPL", reports, "latest")
        assert result == b""

    def test_empty_reports(self):
        result = format_bulk_stocks_fundamental_balance_sheet("AAPL", [], "latest")
        assert result == b""


class TestFormatBulkStocksFundamentalCashFlow:
    def test_formats_cash_flow(self):
        reports = [
            {
                "endDate": "2025-03-31",
                "report": {
                    "cf": [
                        {"concept": "NetCashProvidedByUsedInOperatingActivities", "label": "Op CF", "value": 80000000},
                        {"concept": "NetCashProvidedByUsedInInvestingActivities", "label": "Inv CF", "value": -30000000},
                        {"concept": "NetCashProvidedByUsedInFinancingActivities", "label": "Fin CF", "value": -20000000},
                        {"concept": "NetIncomeLoss", "label": "Net Income", "value": 50000000},
                    ]
                },
            }
        ]
        result = format_bulk_stocks_fundamental_cash_flow("AAPL", reports, "latest")
        decoded = result.decode("utf-8")
        assert "quaks_stocks-fundamental-cash-flow_latest" in decoded
        lines = decoded.strip().split("\n")
        doc = json.loads(lines[1])
        assert doc["operating_cashflow"] == 80000000
        assert doc["cashflow_from_investment"] == -30000000
        assert doc["net_income"] == 50000000

    def test_skips_report_without_cf(self):
        reports = [{"endDate": "2025-03-31", "report": {"cf": []}}]
        result = format_bulk_stocks_fundamental_cash_flow("AAPL", reports, "latest")
        assert result == b""

    def test_empty_reports(self):
        result = format_bulk_stocks_fundamental_cash_flow("AAPL", [], "latest")
        assert result == b""


class TestFormatBulkStocksFundamentalEarningsEstimates:
    def test_formats_estimates(self):
        eps_data = [
            {
                "period": "2025-03-31",
                "freq": "quarterly",
                "epsAvg": 1.5,
                "epsHigh": 2.0,
                "epsLow": 1.0,
                "numberAnalysts": 30,
            }
        ]
        revenue_data = [
            {
                "period": "2025-03-31",
                "revenueAvg": 100000000,
                "revenueHigh": 120000000,
                "revenueLow": 80000000,
                "numberAnalysts": 25,
            }
        ]
        result = format_bulk_stocks_fundamental_earnings_estimates("AAPL", eps_data, revenue_data, "latest")
        decoded = result.decode("utf-8")
        assert "quaks_stocks-fundamental-estimated-earnings_latest" in decoded
        lines = decoded.strip().split("\n")
        doc = json.loads(lines[1])
        assert doc["eps_estimate_average"] == 1.5
        assert doc["horizon"] == "3month"
        assert doc["revenue_estimate_average"] == 100000000

    def test_annual_frequency(self):
        eps_data = [{"period": "2025-12-31", "freq": "annual", "epsAvg": 6.0}]
        result = format_bulk_stocks_fundamental_earnings_estimates("AAPL", eps_data, [], "latest")
        lines = result.decode("utf-8").strip().split("\n")
        doc = json.loads(lines[1])
        assert doc["horizon"] == "12month"

    def test_empty_data(self):
        result = format_bulk_stocks_fundamental_earnings_estimates("AAPL", [], [], "latest")
        assert result == b""

    def test_no_matching_revenue(self):
        eps_data = [{"period": "2025-03-31", "freq": "quarterly", "epsAvg": 1.0}]
        result = format_bulk_stocks_fundamental_earnings_estimates("AAPL", eps_data, [], "latest")
        lines = result.decode("utf-8").strip().split("\n")
        doc = json.loads(lines[1])
        assert doc["revenue_estimate_average"] is None


class TestFormatBulkMarketsNews:
    def test_formats_news(self):
        df = pd.DataFrame({
            "url": ["https://example.com/news1"],
            "created_at": ["2025-01-10T14:30:00Z"],
            "images": [[]],
            "headline": ["Tech Rally"],
            "author": ["Reporter"],
            "summary": ["Stocks are up"],
            "content": ["Full article content"],
            "symbols": [["AAPL", "MSFT"]],
            "source": ["reuters"],
        })
        result = format_bulk_markets_news(df, "latest")
        decoded = result.decode("utf-8")
        assert "quaks_markets-news_latest" in decoded
        assert "Tech Rally" in decoded
        assert "reuters" in decoded


class TestPostToX:
    @patch("app.utils.data_ingestion_utils.OAuth1Session")
    def test_successful_post(self, mock_oauth_cls):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"data": {"id": "12345"}}
        mock_session.post.return_value = mock_response
        mock_oauth_cls.return_value = mock_session

        result = post_to_x(
            "Summary text",
            "https://example.com/article",
            "ck", "cs", "at", "ats",
        )
        assert result is not None
        assert result["data"]["id"] == "12345"

    @patch("app.utils.data_ingestion_utils.OAuth1Session")
    def test_failed_post(self, mock_oauth_cls):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_session.post.return_value = mock_response
        mock_oauth_cls.return_value = mock_session

        result = post_to_x(
            "Summary",
            "https://example.com",
            "ck", "cs", "at", "ats",
        )
        assert result is None

    def test_empty_summary_returns_none(self):
        result = post_to_x("", "https://example.com", "ck", "cs", "at", "ats")
        assert result is None

    def test_whitespace_summary_returns_none(self):
        result = post_to_x("   ", "https://example.com", "ck", "cs", "at", "ats")
        assert result is None

    @patch("app.utils.data_ingestion_utils.OAuth1Session")
    def test_long_summary_truncated(self, mock_oauth_cls):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"data": {"id": "12345"}}
        mock_session.post.return_value = mock_response
        mock_oauth_cls.return_value = mock_session

        long_summary = "A" * 500
        result = post_to_x(
            long_summary,
            "https://example.com/article",
            "ck", "cs", "at", "ats",
        )
        assert result is not None
        call_args = mock_session.post.call_args
        tweet_text = call_args[1]["json"]["text"]
        assert len(tweet_text) <= 280


class TestFinnhubGet:
    @patch("app.utils.data_ingestion_utils.requests.get")
    @patch("app.utils.data_ingestion_utils._finnhub_request_times", [])
    def test_basic_request(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        with patch.dict("os.environ", {"FINNHUB_API_KEY": "test_key"}):
            result = _finnhub_get("/test/path", {"symbol": "AAPL"})
        assert result == {"data": []}


class TestEsBulkPost:
    @patch("app.utils.data_ingestion_utils.requests.post")
    def test_posts_data(self, mock_post):
        mock_response = MagicMock()
        mock_post.return_value = mock_response

        with patch.dict("os.environ", {"ELASTICSEARCH_URL": "http://es:9200", "ELASTICSEARCH_API_KEY": "key"}):
            result = _es_bulk_post(b"test data")
        assert result is mock_response
