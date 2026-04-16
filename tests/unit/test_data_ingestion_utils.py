import math

import pandas as pd

from app.utils.data_ingestion_utils import (
    _find_financial_value,
    _find_financial_value_multi,
    _safe_float,
    _safe_int,
    _epoch_to_date,
    _epoch_to_month_name,
    _es_headers,
    format_bulk_stocks_eod,
    _FINNHUB_FINANCIALS_REPORTED_PATH,
)


def test_finnhub_financials_reported_path_constant():
    assert _FINNHUB_FINANCIALS_REPORTED_PATH == "/stock/financials-reported"


class TestSafeFloat:
    def test_valid_float(self):
        assert _safe_float(3.14) == 3.14

    def test_valid_int(self):
        assert _safe_float(42) == 42.0

    def test_none_returns_none(self):
        assert _safe_float(None) is None

    def test_nan_returns_none(self):
        assert _safe_float(float("nan")) is None

    def test_inf_returns_none(self):
        assert _safe_float(float("inf")) is None

    def test_string_number(self):
        assert _safe_float("3.14") == 3.14

    def test_invalid_string_returns_none(self):
        assert _safe_float("not-a-number") is None

    def test_nat_type_returns_none(self):
        assert _safe_float(pd.NaT) is None


class TestSafeInt:
    def test_valid_int(self):
        assert _safe_int(42) == 42

    def test_valid_float(self):
        assert _safe_int(3.7) == 3

    def test_none_returns_none(self):
        assert _safe_int(None) is None

    def test_nan_returns_none(self):
        assert _safe_int(float("nan")) is None


class TestEpochToDate:
    def test_valid_epoch(self):
        result = _epoch_to_date(1704067200)  # 2024-01-01
        assert result is not None
        assert "2024" in result

    def test_none_returns_none(self):
        assert _epoch_to_date(None) is None

    def test_invalid_epoch_returns_none(self):
        assert _epoch_to_date("bad") is None


class TestEpochToMonthName:
    def test_valid_epoch(self):
        result = _epoch_to_month_name(1704067200)  # January 2024
        assert result == "January"

    def test_none_returns_none(self):
        assert _epoch_to_month_name(None) is None

    def test_invalid_returns_none(self):
        assert _epoch_to_month_name("bad") is None


class TestEsHeaders:
    def test_returns_headers_dict(self):
        headers = _es_headers()
        assert "Authorization" in headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/x-ndjson"


class TestFormatBulkStocksEod:
    def test_formats_dataframe(self):
        df = pd.DataFrame({
            "t": ["2025-01-10T00:00:00Z"],
            "o": [150.0],
            "c": [152.0],
            "h": [155.0],
            "l": [149.0],
            "v": [1000000],
        })
        result = format_bulk_stocks_eod("AAPL", df, "latest")
        assert b"AAPL" in result
        assert b"quaks_stocks-eod_latest" in result

    def test_skips_rows_without_open_close(self):
        df = pd.DataFrame({
            "t": ["2025-01-10"],
            "o": [None],
            "c": [None],
            "h": [155.0],
            "l": [149.0],
            "v": [1000000],
        })
        result = format_bulk_stocks_eod("AAPL", df, "latest")
        assert result == b"\n"

    def test_handles_date_without_T(self):
        df = pd.DataFrame({
            "t": ["2025-01-10"],
            "o": [150.0],
            "c": [152.0],
            "h": [155.0],
            "l": [149.0],
            "v": [1000000],
        })
        result = format_bulk_stocks_eod("AAPL", df, "test")
        assert b"2025-01-10" in result


def test_find_financial_value_empty_items():
    assert _find_financial_value([], "Revenue") is None
    assert _find_financial_value(None, "Revenue") is None


def test_find_financial_value_by_concept():
    items = [{"concept": "RevenueFromContractWithCustomer", "label": "Revenue", "value": 100.5}]
    result = _find_financial_value(items, "RevenueFromContract")
    assert result == 100.5


def test_find_financial_value_by_label():
    items = [{"concept": "Other", "label": "Total Revenue", "value": 200.0}]
    result = _find_financial_value(items, "NonMatch", label_contains="Total Revenue")
    assert result == 200.0


def test_find_financial_value_no_match():
    items = [{"concept": "Other", "label": "Other", "value": 50}]
    result = _find_financial_value(items, "NonExistent")
    assert result is None


def test_find_financial_value_multi_first_match():
    items = [{"concept": "NetIncome", "label": "Net Income", "value": 300.0}]
    result = _find_financial_value_multi(items, ["Revenue", "NetIncome"])
    assert result == 300.0


def test_find_financial_value_multi_no_match():
    items = [{"concept": "Other", "label": "Other", "value": 10}]
    result = _find_financial_value_multi(items, ["NonExistent", "AlsoNonExistent"])
    assert result is None
