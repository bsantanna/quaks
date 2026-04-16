from app.utils.data_ingestion_utils import (
    _find_financial_value,
    _find_financial_value_multi,
    _FINNHUB_FINANCIALS_REPORTED_PATH,
)


def test_finnhub_financials_reported_path_constant():
    assert _FINNHUB_FINANCIALS_REPORTED_PATH == "/stock/financials-reported"


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
