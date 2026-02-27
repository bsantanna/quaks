import hashlib
import math
import os
import requests
import json
import pandas as pd
from datetime import datetime
from requests import Response


def _safe_float(val):
    if val is None or (hasattr(val, '__class__') and val.__class__.__name__ == 'NaTType'):
        return None
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else f
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    f = _safe_float(val)
    return int(f) if f is not None else None


def _epoch_to_date(epoch_val):
    if epoch_val is None:
        return None
    try:
        return datetime.fromtimestamp(int(epoch_val)).strftime('%Y-%m-%d')
    except (ValueError, TypeError, OSError):
        return None


def _epoch_to_month_name(epoch_val):
    if epoch_val is None:
        return None
    try:
        return datetime.fromtimestamp(int(epoch_val)).strftime('%B')
    except (ValueError, TypeError, OSError):
        return None


def _finnhub_get(path: str, params: dict = None) -> dict:
    finnhub_api_key = os.environ.get('FINNHUB_API_KEY')
    base_url = "https://finnhub.io/api/v1"
    if params is None:
        params = {}
    params['token'] = finnhub_api_key
    response = requests.get(f"{base_url}{path}", params=params)
    return response.json()


def _es_headers():
    es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')
    return {
        'Authorization': f'ApiKey {es_api_key}',
        'Content-Type': 'application/x-ndjson'
    }


def _es_bulk_post(data: bytes) -> Response:
    es_url = os.environ.get('ELASTICSEARCH_URL')
    return requests.post(
        url=f"{es_url}/_bulk",
        headers=_es_headers(),
        data=data
    )


# ---------------------------------------------------------------------------
# Helper: extract a value from financials-reported line items
# ---------------------------------------------------------------------------

def _find_financial_value(items: list, concept: str, label_contains: str = None) -> float:
    """Search a list of SEC filing line items for a matching concept or label."""
    if not items:
        return None
    for item in items:
        c = item.get('concept', '')
        lbl = item.get('label', '')
        if concept and concept.lower() in c.lower():
            return _safe_float(item.get('value'))
        if label_contains and label_contains.lower() in lbl.lower():
            return _safe_float(item.get('value'))
    return None


def _find_financial_value_multi(items: list, concepts: list) -> float:
    """Try multiple concept names, return first match."""
    for concept in concepts:
        val = _find_financial_value(items, concept)
        if val is not None:
            return val
    return None


# ---------------------------------------------------------------------------
# Stocks EOD (Alpaca — unchanged)
# ---------------------------------------------------------------------------

def format_bulk_stocks_eod(ticker: str, df: pd.DataFrame, index_suffix: str, source: str) -> bytes:
    index_name = f"quaks_stocks-eod_{index_suffix}"
    lines = []

    for _, row in df.iterrows():
        date_reference = row.get('timestamp') if source == "alphavantage" else row.get('t').split('T')[0]
        open_ = row.get('open') if source == "alphavantage" else row.get('o')
        close = row.get('close') if source == "alphavantage" else row.get('c')
        high = row.get('high') if source == "alphavantage" else row.get('h')
        low = row.get('low') if source == "alphavantage" else row.get('l')
        volume = row.get('volume') if source == "alphavantage" else row.get('v')

        if open_ is None or close is None:
            continue
        id_str = f"{ticker}_{str(date_reference)}"

        meta = {"index": {"_index": index_name, "_id": id_str}}
        doc = {
            "key_ticker": ticker,
            "date_reference": date_reference,
            "val_open": float(open_),
            "val_close": float(close) if close is not None else None,
            "val_high": float(high) if high is not None else None,
            "val_low": float(low) if low is not None else None,
            "val_volume": int(volume) if volume is not None else None,
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8")


def ingest_stocks_eod(ticker: str, index_suffix="latest", source="alpaca") -> Response:
    es_url = os.environ.get('ELASTICSEARCH_URL')
    es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')

    ticker_daily_time_series = None

    if source == "alpaca":
        now = datetime.now()
        yesterday = now.replace(day=now.day - 1)
        back_one_year = now.replace(year=now.year - 1)
        alpaca_api_key = os.environ.get('APCA-API-KEY-ID')
        alpaca_api_secret = os.environ.get('APCA-API-SECRET-KEY')
        alpaca_time_series_url = f"https://data.alpaca.markets/v2/stocks/{ticker}/bars?timeframe=1D&start={back_one_year.strftime('%Y-%m-%d')}&end={yesterday.strftime('%Y-%m-%d')}&adjustment=all"
        response = requests.get(alpaca_time_series_url, headers={
            "accept": "application/json",
            "APCA-API-KEY-ID": alpaca_api_key,
            "APCA-API-SECRET-KEY": alpaca_api_secret
        })
        ticker_daily_time_series = pd.json_normalize(response.json().get('bars'))

    return requests.post(
        url=f"{es_url}/_bulk",
        headers={
            'Authorization': f'ApiKey {es_api_key}',
            'Content-Type': 'application/x-ndjson'
        },
        data=format_bulk_stocks_eod(ticker, ticker_daily_time_series, index_suffix, source)
    )


# ---------------------------------------------------------------------------
# Insider Trades (Finnhub)
# ---------------------------------------------------------------------------

def format_bulk_stocks_insider_trades(ticker: str, data: list, index_suffix: str) -> bytes:
    index_name = f"quaks_stocks-insider-trades_{index_suffix}"
    lines = []

    for item in data:
        name = item.get('name', '')
        txn_date = item.get('transactionDate')
        txn_code = item.get('transactionCode', '')
        txn_price = _safe_float(item.get('transactionPrice'))
        change = _safe_float(item.get('change'))

        if not txn_date:
            continue

        # Map transaction codes: P=Purchase, S=Sale, A=Grant/Award
        if txn_code in ('P', 'A'):
            acquisition_or_disposal = "Acquisition"
        elif txn_code == 'S':
            acquisition_or_disposal = "Disposal"
        else:
            acquisition_or_disposal = "Unknown"

        id_str = f"{ticker}_{txn_date}_{name[:20].replace(' ', '_')}"

        meta = {"index": {"_index": index_name, "_id": id_str}}
        doc = {
            "key_ticker": ticker,
            "date_reference": txn_date,
            "text_executive_name": name,
            "text_executive_title": "",
            "key_acquisition_disposal": acquisition_or_disposal,
            "val_share_quantity": abs(change) if change else None,
            "val_share_price": txn_price,
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8") if lines else b""


def ingest_stocks_insider_trades(ticker: str, cutoff_days=365, index_suffix="latest") -> Response:
    now = datetime.now()
    from_date = (now - pd.Timedelta(days=cutoff_days)).strftime('%Y-%m-%d')
    to_date = now.strftime('%Y-%m-%d')

    result = _finnhub_get('/stock/insider-transactions', {
        'symbol': ticker,
        'from': from_date,
        'to': to_date,
    })
    data = result.get('data', [])

    if not data:
        return _es_bulk_post(b"\n")

    return _es_bulk_post(
        format_bulk_stocks_insider_trades(ticker, data, index_suffix)
    )


# ---------------------------------------------------------------------------
# Stocks Metadata (Finnhub)
# ---------------------------------------------------------------------------

def format_bulk_stocks_metadata(ticker: str, profile: dict, index_suffix: str) -> bytes:
    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quaks_stocks-metadata_{index_suffix}"

    id_str = f"{ticker}_{today}"

    meta = {"index": {"_index": index_name, "_id": id_str}}

    market_cap_millions = _safe_float(profile.get('marketCapitalization'))
    market_cap = _safe_int(market_cap_millions * 1_000_000) if market_cap_millions else None

    shares_millions = _safe_float(profile.get('shareOutstanding'))
    shares = _safe_int(shares_millions * 1_000_000) if shares_millions else None

    doc = {
        "key_ticker": profile.get('ticker', ticker),
        "asset_type": None,
        "name": profile.get('name'),
        "description": None,
        "cik": None,
        "exchange": profile.get('exchange'),
        "currency": profile.get('currency'),
        "country": profile.get('country'),
        "sector": profile.get('finnhubIndustry'),
        "industry": profile.get('finnhubIndustry'),
        "address": None,
        "official_site": profile.get('weburl'),
        "fiscal_year_end": None,
        "latest_quarter": None,
        "market_capitalization": market_cap,
        "ebitda": None,
        "pe_ratio": None,
        "peg_ratio": None,
        "book_value": None,
        "dividend_per_share": None,
        "dividend_yield": None,
        "eps": None,
        "revenue_per_share_ttm": None,
        "profit_margin": None,
        "operating_margin_ttm": None,
        "return_on_assets_ttm": None,
        "return_on_equity_ttm": None,
        "revenue_ttm": None,
        "gross_profit_ttm": None,
        "diluted_eps_ttm": None,
        "quarterly_earnings_growth_yoy": None,
        "quarterly_revenue_growth_yoy": None,
        "analyst_target_price": None,
        "analyst_rating_strong_buy": None,
        "analyst_rating_buy": None,
        "analyst_rating_hold": None,
        "analyst_rating_sell": None,
        "analyst_rating_strong_sell": None,
        "trailing_pe": None,
        "forward_pe": None,
        "price_to_sales_ratio_ttm": None,
        "price_to_book_ratio": None,
        "ev_to_revenue": None,
        "ev_to_ebitda": None,
        "beta": None,
        "week_52_high": None,
        "week_52_low": None,
        "moving_average_50_day": None,
        "moving_average_200_day": None,
        "shares_outstanding": shares,
        "shares_float": None,
        "percent_insiders": None,
        "percent_institutions": None,
        "dividend_date": None,
        "ex_dividend_date": None,
    }

    lines = [json.dumps(meta), json.dumps(doc)]
    return (("\n".join(lines)) + "\n").encode("utf-8")


def _enrich_metadata_with_metrics(ticker: str, doc: dict) -> dict:
    """Enrich metadata doc with basic metrics from Finnhub."""
    metrics = _finnhub_get('/stock/metric', {
        'symbol': ticker,
        'metric': 'all',
    })
    m = metrics.get('metric', {})
    if m:
        doc["pe_ratio"] = _safe_float(m.get('peBasicExclExtraTTM'))
        doc["trailing_pe"] = _safe_float(m.get('peBasicExclExtraTTM'))
        doc["forward_pe"] = _safe_float(m.get('peExclExtraAnnual'))
        doc["peg_ratio"] = _safe_float(m.get('pegRatio'))
        doc["book_value"] = _safe_float(m.get('bookValuePerShareQuarterly'))
        doc["dividend_per_share"] = _safe_float(m.get('dividendPerShareAnnual'))
        doc["dividend_yield"] = _safe_float(m.get('dividendYieldIndicatedAnnual'))
        doc["eps"] = _safe_float(m.get('epsBasicExclExtraItemsTTM'))
        doc["revenue_per_share_ttm"] = _safe_float(m.get('revenuePerShareTTM'))
        doc["profit_margin"] = _safe_float(m.get('netProfitMarginTTM'))
        doc["operating_margin_ttm"] = _safe_float(m.get('operatingMarginTTM'))
        doc["return_on_assets_ttm"] = _safe_float(m.get('roaTTM'))
        doc["return_on_equity_ttm"] = _safe_float(m.get('roeTTM'))
        doc["revenue_ttm"] = _safe_int(m.get('revenueTTM'))
        doc["ebitda"] = _safe_int(m.get('ebitdTTM'))
        doc["beta"] = _safe_float(m.get('beta'))
        doc["week_52_high"] = _safe_float(m.get('52WeekHigh'))
        doc["week_52_low"] = _safe_float(m.get('52WeekLow'))
        doc["price_to_sales_ratio_ttm"] = _safe_float(m.get('psTTM'))
        doc["price_to_book_ratio"] = _safe_float(m.get('pbQuarterly'))
        doc["ev_to_revenue"] = _safe_float(m.get('enterpriseValueOverRevenueAnnual'))
        doc["ev_to_ebitda"] = _safe_float(m.get('enterpriseValueOverEBITDAAnnual'))
        doc["analyst_target_price"] = _safe_float(m.get('targetMedianPrice'))
        doc["moving_average_50_day"] = _safe_float(m.get('50DayMA'))
        doc["moving_average_200_day"] = _safe_float(m.get('200DayMA'))
    return doc


def ingest_stocks_metadata(ticker: str, index_suffix="latest") -> Response:
    profile = _finnhub_get('/stock/profile2', {'symbol': ticker})

    if not profile or not profile.get('ticker'):
        return _es_bulk_post(b"\n")

    data = format_bulk_stocks_metadata(ticker, profile, index_suffix)

    # Decode, enrich with metrics, re-encode
    lines = data.decode('utf-8').strip().split('\n')
    if len(lines) >= 2:
        doc = json.loads(lines[1])
        doc = _enrich_metadata_with_metrics(ticker, doc)
        lines[1] = json.dumps(doc)
        data = (("\n".join(lines)) + "\n").encode("utf-8")

    return _es_bulk_post(data)


# ---------------------------------------------------------------------------
# Fundamental: Income Statement (Finnhub financials-reported)
# ---------------------------------------------------------------------------

def format_bulk_stocks_fundamental_income_statement(ticker: str, reports: list, index_suffix: str) -> bytes:
    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quaks_stocks-fundamental-income-statement_{index_suffix}"
    lines = []

    for report in reports:
        fiscal_date_ending = report.get('endDate', '').split(' ')[0].split('T')[0]
        if not fiscal_date_ending:
            continue

        ic = report.get('report', {}).get('ic', [])
        if not ic:
            continue

        id_str = f"{ticker}_{fiscal_date_ending}"
        meta = {"index": {"_index": index_name, "_id": id_str}}

        doc = {
            "key_ticker": ticker,
            "fiscal_date_ending": fiscal_date_ending,
            "reported_currency": "USD",
            "total_revenue": _safe_int(_find_financial_value_multi(ic, [
                'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax',
                'SalesRevenueNet', 'Revenue', 'NetRevenues',
            ])),
            "gross_profit": _safe_int(_find_financial_value_multi(ic, [
                'GrossProfit',
            ])),
            "cost_of_revenue": _safe_int(_find_financial_value_multi(ic, [
                'CostOfRevenue', 'CostOfGoodsAndServicesSold', 'CostOfGoodsSold',
            ])),
            "cost_of_goods_and_services_sold": _safe_int(_find_financial_value_multi(ic, [
                'CostOfGoodsAndServicesSold', 'CostOfRevenue', 'CostOfGoodsSold',
            ])),
            "operating_income": _safe_int(_find_financial_value_multi(ic, [
                'OperatingIncomeLoss', 'OperatingIncome',
            ])),
            "selling_general_and_administrative": _safe_int(_find_financial_value_multi(ic, [
                'SellingGeneralAndAdministrativeExpense',
            ])),
            "research_and_development": _safe_int(_find_financial_value_multi(ic, [
                'ResearchAndDevelopmentExpense',
            ])),
            "operating_expenses": _safe_int(_find_financial_value_multi(ic, [
                'OperatingExpenses', 'CostsAndExpenses',
            ])),
            "investment_income_net": _safe_float(_find_financial_value_multi(ic, [
                'InvestmentIncomeNet',
            ])),
            "net_interest_income": _safe_int(_find_financial_value_multi(ic, [
                'InterestIncomeExpenseNet', 'NetInterestIncome',
            ])),
            "interest_income": _safe_int(_find_financial_value_multi(ic, [
                'InterestIncome', 'InvestmentIncomeInterest',
            ])),
            "interest_expense": _safe_int(_find_financial_value_multi(ic, [
                'InterestExpense',
            ])),
            "non_interest_income": _safe_float(_find_financial_value_multi(ic, [
                'NoninterestIncome', 'OtherNonoperatingIncomeExpense',
            ])),
            "other_non_operating_income": _safe_float(_find_financial_value_multi(ic, [
                'OtherNonoperatingIncomeExpense', 'NonoperatingIncomeExpense',
            ])),
            "depreciation": _safe_float(_find_financial_value_multi(ic, [
                'Depreciation', 'DepreciationAmortizationAndAccretion',
            ])),
            "depreciation_and_amortization": _safe_int(_find_financial_value_multi(ic, [
                'DepreciationAndAmortization', 'DepreciationAmortizationAndAccretion',
            ])),
            "income_before_tax": _safe_int(_find_financial_value_multi(ic, [
                'IncomeLossFromContinuingOperationsBeforeIncomeTaxes',
                'IncomeLossBeforeIncomeTax', 'IncomeBeforeTax',
            ])),
            "income_tax_expense": _safe_int(_find_financial_value_multi(ic, [
                'IncomeTaxExpenseBenefit',
            ])),
            "interest_and_debt_expense": _safe_float(_find_financial_value_multi(ic, [
                'InterestExpense', 'InterestAndDebtExpense',
            ])),
            "net_income_from_continuing_operations": _safe_int(_find_financial_value_multi(ic, [
                'IncomeLossFromContinuingOperations',
                'NetIncomeLossFromContinuingOperations',
            ])),
            "comprehensive_income_net_of_tax": _safe_float(_find_financial_value_multi(ic, [
                'ComprehensiveIncomeNetOfTax',
            ])),
            "ebit": _safe_int(_find_financial_value_multi(ic, [
                'OperatingIncomeLoss', 'OperatingIncome',
            ])),
            "ebitda": None,
            "net_income": _safe_int(_find_financial_value_multi(ic, [
                'NetIncomeLoss', 'NetIncome', 'ProfitLoss',
            ])),
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8") if lines else b""


def ingest_stocks_fundamental_income_statement(ticker: str, cutoff_days=3650, index_suffix="latest") -> Response:
    result = _finnhub_get('/stock/financials-reported', {
        'symbol': ticker,
        'freq': 'quarterly',
    })
    reports = result.get('data', [])

    if not reports:
        return _es_bulk_post(b"\n")

    # Filter by cutoff
    cutoff_date = (datetime.now() - pd.Timedelta(days=cutoff_days)).strftime('%Y-%m-%d')
    reports = [r for r in reports if (r.get('endDate', '') or '') >= cutoff_date]

    return _es_bulk_post(
        format_bulk_stocks_fundamental_income_statement(ticker, reports, index_suffix)
    )


# ---------------------------------------------------------------------------
# Fundamental: Balance Sheet (Finnhub financials-reported)
# ---------------------------------------------------------------------------

def format_bulk_stocks_fundamental_balance_sheet(ticker: str, reports: list, index_suffix: str) -> bytes:
    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quaks_stocks-fundamental-balance-sheet_{index_suffix}"
    lines = []

    for report in reports:
        fiscal_date_ending = report.get('endDate', '').split(' ')[0].split('T')[0]
        if not fiscal_date_ending:
            continue

        bs = report.get('report', {}).get('bs', [])
        if not bs:
            continue

        id_str = f"{ticker}_{fiscal_date_ending}"
        meta = {"index": {"_index": index_name, "_id": id_str}}

        doc = {
            "key_ticker": ticker,
            "fiscal_date_ending": fiscal_date_ending,
            "reported_currency": "USD",
            "total_assets": _safe_int(_find_financial_value_multi(bs, [
                'Assets',
            ])),
            "total_current_assets": _safe_int(_find_financial_value_multi(bs, [
                'AssetsCurrent',
            ])),
            "cash_and_cash_equivalents_at_carrying_value": _safe_int(_find_financial_value_multi(bs, [
                'CashAndCashEquivalentsAtCarryingValue', 'CashAndCashEquivalents',
            ])),
            "cash_and_short_term_investments": _safe_int(_find_financial_value_multi(bs, [
                'CashCashEquivalentsAndShortTermInvestments',
            ])),
            "inventory": _safe_int(_find_financial_value_multi(bs, [
                'InventoryNet', 'Inventory',
            ])),
            "current_net_receivables": _safe_int(_find_financial_value_multi(bs, [
                'AccountsReceivableNetCurrent', 'ReceivablesNetCurrent',
            ])),
            "total_non_current_assets": _safe_int(_find_financial_value_multi(bs, [
                'AssetsNoncurrent',
            ])),
            "property_plant_equipment": _safe_int(_find_financial_value_multi(bs, [
                'PropertyPlantAndEquipmentNet',
            ])),
            "accumulated_depreciation_amortization_ppe": _safe_int(_find_financial_value_multi(bs, [
                'AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment',
            ])),
            "intangible_assets": _safe_int(_find_financial_value_multi(bs, [
                'IntangibleAssetsNetIncludingGoodwill',
            ])),
            "intangible_assets_excluding_goodwill": _safe_int(_find_financial_value_multi(bs, [
                'IntangibleAssetsNetExcludingGoodwill', 'FiniteLivedIntangibleAssetsNet',
            ])),
            "goodwill": _safe_int(_find_financial_value_multi(bs, [
                'Goodwill',
            ])),
            "investments": _safe_int(_find_financial_value_multi(bs, [
                'Investments', 'ShortTermInvestments',
            ])),
            "long_term_investments": _safe_int(_find_financial_value_multi(bs, [
                'LongTermInvestments', 'MarketableSecuritiesNoncurrent',
            ])),
            "short_term_investments": _safe_int(_find_financial_value_multi(bs, [
                'ShortTermInvestments', 'MarketableSecuritiesCurrent',
            ])),
            "other_current_assets": _safe_int(_find_financial_value_multi(bs, [
                'OtherAssetsCurrent',
            ])),
            "other_non_current_assets": _safe_int(_find_financial_value_multi(bs, [
                'OtherAssetsNoncurrent',
            ])),
            "total_liabilities": _safe_int(_find_financial_value_multi(bs, [
                'Liabilities', 'LiabilitiesAndStockholdersEquity',
            ])),
            "total_current_liabilities": _safe_int(_find_financial_value_multi(bs, [
                'LiabilitiesCurrent',
            ])),
            "current_accounts_payable": _safe_int(_find_financial_value_multi(bs, [
                'AccountsPayableCurrent', 'AccountsPayable',
            ])),
            "deferred_revenue": _safe_int(_find_financial_value_multi(bs, [
                'DeferredRevenueCurrent', 'DeferredRevenue', 'ContractWithCustomerLiabilityCurrent',
            ])),
            "current_debt": _safe_int(_find_financial_value_multi(bs, [
                'DebtCurrent', 'ShortTermBorrowings', 'CommercialPaper',
            ])),
            "short_term_debt": _safe_int(_find_financial_value_multi(bs, [
                'ShortTermBorrowings', 'DebtCurrent', 'CommercialPaper',
            ])),
            "total_non_current_liabilities": _safe_int(_find_financial_value_multi(bs, [
                'LiabilitiesNoncurrent',
            ])),
            "capital_lease_obligations": _safe_int(_find_financial_value_multi(bs, [
                'CapitalLeaseObligations', 'OperatingLeaseLiability',
            ])),
            "long_term_debt": _safe_int(_find_financial_value_multi(bs, [
                'LongTermDebtNoncurrent', 'LongTermDebt',
            ])),
            "current_long_term_debt": _safe_int(_find_financial_value_multi(bs, [
                'LongTermDebtCurrent',
            ])),
            "long_term_debt_noncurrent": _safe_int(_find_financial_value_multi(bs, [
                'LongTermDebtNoncurrent', 'LongTermDebt',
            ])),
            "short_long_term_debt_total": _safe_int(_find_financial_value_multi(bs, [
                'DebtAndCapitalLeaseObligations', 'LongTermDebtAndCapitalLeaseObligations',
            ])),
            "other_current_liabilities": _safe_int(_find_financial_value_multi(bs, [
                'OtherLiabilitiesCurrent',
            ])),
            "other_non_current_liabilities": _safe_int(_find_financial_value_multi(bs, [
                'OtherLiabilitiesNoncurrent',
            ])),
            "total_shareholder_equity": _safe_int(_find_financial_value_multi(bs, [
                'StockholdersEquity',
            ])),
            "treasury_stock": _safe_int(_find_financial_value_multi(bs, [
                'TreasuryStockValue', 'TreasuryStockShares',
            ])),
            "retained_earnings": _safe_int(_find_financial_value_multi(bs, [
                'RetainedEarningsAccumulatedDeficit',
            ])),
            "common_stock": _safe_int(_find_financial_value_multi(bs, [
                'CommonStockValue', 'CommonStocksIncludingAdditionalPaidInCapital',
            ])),
            "common_stock_shares_outstanding": _safe_int(_find_financial_value_multi(bs, [
                'CommonStockSharesOutstanding',
            ])),
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8") if lines else b""


def ingest_stocks_fundamental_balance_sheet(ticker: str, cutoff_days=3650, index_suffix="latest") -> Response:
    result = _finnhub_get('/stock/financials-reported', {
        'symbol': ticker,
        'freq': 'quarterly',
    })
    reports = result.get('data', [])

    if not reports:
        return _es_bulk_post(b"\n")

    cutoff_date = (datetime.now() - pd.Timedelta(days=cutoff_days)).strftime('%Y-%m-%d')
    reports = [r for r in reports if (r.get('endDate', '') or '') >= cutoff_date]

    return _es_bulk_post(
        format_bulk_stocks_fundamental_balance_sheet(ticker, reports, index_suffix)
    )


# ---------------------------------------------------------------------------
# Fundamental: Cash Flow (Finnhub financials-reported)
# ---------------------------------------------------------------------------

def format_bulk_stocks_fundamental_cash_flow(ticker: str, reports: list, index_suffix: str) -> bytes:
    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quaks_stocks-fundamental-cash-flow_{index_suffix}"
    lines = []

    for report in reports:
        fiscal_date_ending = report.get('endDate', '').split(' ')[0].split('T')[0]
        if not fiscal_date_ending:
            continue

        cf = report.get('report', {}).get('cf', [])
        if not cf:
            continue

        id_str = f"{ticker}_{fiscal_date_ending}"
        meta = {"index": {"_index": index_name, "_id": id_str}}

        doc = {
            "key_ticker": ticker,
            "fiscal_date_ending": fiscal_date_ending,
            "reported_currency": "USD",
            "operating_cashflow": _safe_int(_find_financial_value_multi(cf, [
                'NetCashProvidedByUsedInOperatingActivities',
                'NetCashProvidedByOperatingActivities',
            ])),
            "payments_for_operating_activities": None,
            "proceeds_from_operating_activities": None,
            "change_in_operating_liabilities": _safe_int(_find_financial_value_multi(cf, [
                'IncreaseDecreaseInAccountsPayable',
                'IncreaseDecreaseInOtherOperatingLiabilities',
            ])),
            "change_in_operating_assets": _safe_int(_find_financial_value_multi(cf, [
                'IncreaseDecreaseInOtherOperatingAssets',
            ])),
            "depreciation_depletion_and_amortization": _safe_int(_find_financial_value_multi(cf, [
                'DepreciationDepletionAndAmortization', 'Depreciation',
                'DepreciationAndAmortization',
            ])),
            "capital_expenditures": _safe_int(_find_financial_value_multi(cf, [
                'PaymentsToAcquirePropertyPlantAndEquipment',
                'CapitalExpenditures',
            ])),
            "change_in_receivables": _safe_int(_find_financial_value_multi(cf, [
                'IncreaseDecreaseInAccountsReceivable',
            ])),
            "change_in_inventory": _safe_int(_find_financial_value_multi(cf, [
                'IncreaseDecreaseInInventories',
            ])),
            "profit_loss": _safe_int(_find_financial_value_multi(cf, [
                'NetIncomeLoss', 'ProfitLoss',
            ])),
            "cashflow_from_investment": _safe_int(_find_financial_value_multi(cf, [
                'NetCashProvidedByUsedInInvestingActivities',
            ])),
            "cashflow_from_financing": _safe_int(_find_financial_value_multi(cf, [
                'NetCashProvidedByUsedInFinancingActivities',
            ])),
            "proceeds_from_repayments_of_short_term_debt": _safe_int(_find_financial_value_multi(cf, [
                'ProceedsFromRepaymentsOfShortTermDebt',
                'RepaymentsOfShortTermDebt',
            ])),
            "payments_for_repurchase_of_common_stock": _safe_int(_find_financial_value_multi(cf, [
                'PaymentsForRepurchaseOfCommonStock',
            ])),
            "payments_for_repurchase_of_equity": _safe_int(_find_financial_value_multi(cf, [
                'PaymentsForRepurchaseOfCommonStock',
                'PaymentsForRepurchaseOfEquity',
            ])),
            "payments_for_repurchase_of_preferred_stock": _safe_int(_find_financial_value_multi(cf, [
                'PaymentsForRepurchaseOfPreferredStockAndPreferenceStock',
            ])),
            "dividend_payout": _safe_int(_find_financial_value_multi(cf, [
                'PaymentsOfDividends', 'PaymentsOfDividendsCommonStock',
            ])),
            "dividend_payout_common_stock": _safe_int(_find_financial_value_multi(cf, [
                'PaymentsOfDividendsCommonStock', 'PaymentsOfDividends',
            ])),
            "dividend_payout_preferred_stock": _safe_int(_find_financial_value_multi(cf, [
                'PaymentsOfDividendsPreferredStockAndPreferenceStock',
            ])),
            "proceeds_from_issuance_of_common_stock": _safe_int(_find_financial_value_multi(cf, [
                'ProceedsFromIssuanceOfCommonStock',
            ])),
            "proceeds_from_issuance_of_long_term_debt_and_capital_securities_net": _safe_int(_find_financial_value_multi(cf, [
                'ProceedsFromIssuanceOfLongTermDebt',
            ])),
            "proceeds_from_issuance_of_preferred_stock": _safe_int(_find_financial_value_multi(cf, [
                'ProceedsFromIssuanceOfPreferredStock',
            ])),
            "proceeds_from_repurchase_of_equity": None,
            "proceeds_from_sale_of_treasury_stock": None,
            "change_in_cash_and_cash_equivalents": _safe_int(_find_financial_value_multi(cf, [
                'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect',
                'CashAndCashEquivalentsPeriodIncreaseDecrease',
            ])),
            "change_in_exchange_rate": _safe_int(_find_financial_value_multi(cf, [
                'EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents',
                'EffectOfExchangeRateOnCashAndCashEquivalents',
            ])),
            "net_income": _safe_int(_find_financial_value_multi(cf, [
                'NetIncomeLoss', 'ProfitLoss',
            ])),
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8") if lines else b""


def ingest_stocks_fundamental_cash_flow(ticker: str, cutoff_days=3650, index_suffix="latest") -> Response:
    result = _finnhub_get('/stock/financials-reported', {
        'symbol': ticker,
        'freq': 'quarterly',
    })
    reports = result.get('data', [])

    if not reports:
        return _es_bulk_post(b"\n")

    cutoff_date = (datetime.now() - pd.Timedelta(days=cutoff_days)).strftime('%Y-%m-%d')
    reports = [r for r in reports if (r.get('endDate', '') or '') >= cutoff_date]

    return _es_bulk_post(
        format_bulk_stocks_fundamental_cash_flow(ticker, reports, index_suffix)
    )


# ---------------------------------------------------------------------------
# Fundamental: Earnings Estimates (Finnhub — unchanged)
# ---------------------------------------------------------------------------

def format_bulk_stocks_fundamental_earnings_estimates(ticker: str, eps_data: list, revenue_data: list, index_suffix: str) -> bytes:
    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quaks_stocks-fundamental-estimated-earnings_{index_suffix}"
    lines = []

    revenue_by_period = {}
    for item in revenue_data:
        period = item.get('period')
        if period:
            revenue_by_period[period] = item

    for item in eps_data:
        period = item.get('period')
        freq = item.get('freq', '')
        date = period or today

        revenue_item = revenue_by_period.get(period, {})

        horizon = freq
        if freq == "quarterly":
            horizon = "3month"
        elif freq == "annual":
            horizon = "12month"

        id_str = f"{ticker}_{date}_{freq}"

        meta = {"index": {"_index": index_name, "_id": id_str}}
        doc = {
            "key_ticker": ticker,
            "date": date,
            "horizon": horizon,
            "eps_estimate_average": _safe_float(item.get('epsAvg')),
            "eps_estimate_high": _safe_float(item.get('epsHigh')),
            "eps_estimate_low": _safe_float(item.get('epsLow')),
            "eps_estimate_analyst_count": _safe_int(item.get('numberAnalysts')),
            "eps_estimate_average_7_days_ago": None,
            "eps_estimate_average_30_days_ago": None,
            "eps_estimate_average_60_days_ago": None,
            "eps_estimate_average_90_days_ago": None,
            "eps_estimate_revision_up_trailing_7_days": None,
            "eps_estimate_revision_down_trailing_7_days": None,
            "eps_estimate_revision_up_trailing_30_days": None,
            "eps_estimate_revision_down_trailing_30_days": None,
            "revenue_estimate_average": _safe_float(revenue_item.get('revenueAvg')),
            "revenue_estimate_high": _safe_float(revenue_item.get('revenueHigh')),
            "revenue_estimate_low": _safe_float(revenue_item.get('revenueLow')),
            "revenue_estimate_analyst_count": _safe_int(revenue_item.get('numberAnalysts')),
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8") if lines else b""


def ingest_stocks_fundamental_earnings_estimates(ticker: str, cutoff_days=3650, index_suffix="latest") -> Response:
    eps_data = _finnhub_get('/stock/eps-estimate', {'symbol': ticker}).get('data', [])
    revenue_data = _finnhub_get('/stock/revenue-estimate', {'symbol': ticker}).get('data', [])

    if not eps_data and not revenue_data:
        return _es_bulk_post(b"\n")

    return _es_bulk_post(
        format_bulk_stocks_fundamental_earnings_estimates(ticker, eps_data, revenue_data, index_suffix)
    )


# ---------------------------------------------------------------------------
# Markets News (Alpaca — unchanged)
# ---------------------------------------------------------------------------

def format_bulk_markets_news(df: pd.DataFrame, index_suffix: str) -> bytes:
    index_name = f"quaks_markets-news_{index_suffix}"
    lines = []

    for _, row in df.iterrows():
        url = row.get('url')
        created_at = row.get('created_at').split('T')[0]
        images = row.get('images')
        headline = row.get('headline')
        author = row.get('author')
        summary = row.get('summary')
        content = row.get('content')
        symbols = row.get('symbols')
        source = row.get('source')

        id_str = f"{hashlib.md5(url.encode('utf-8')).hexdigest()}"
        meta = {"index": {"_index": index_name, "_id": id_str}}

        doc = {
            "key_ticker": symbols,
            "key_url": url,
            "key_source": source,
            "date_reference": created_at,
            "obj_images": images,
            "text_headline": headline,
            "text_author": author,
            "text_summary": summary,
            "text_content": content
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8")


def ingest_markets_news(ticker: str, limit=20, index_suffix="latest") -> Response:
    es_url = os.environ.get('ELASTICSEARCH_URL')
    es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')

    now = datetime.now()
    yesterday = now.replace(day=now.day - 1)
    alpaca_api_key = os.environ.get('APCA-API-KEY-ID')
    alpaca_api_secret = os.environ.get('APCA-API-SECRET-KEY')
    alpaca_time_series_url = f"https://data.alpaca.markets/v1beta1/news?start={yesterday.strftime('%Y-%m-%d')}&symbols={ticker}&limit={limit}&include_content=true&exclude_contentless=true"
    response = requests.get(alpaca_time_series_url, headers={
        "accept": "application/json",
        "APCA-API-KEY-ID": alpaca_api_key,
        "APCA-API-SECRET-KEY": alpaca_api_secret
    })
    ticker_news_series = pd.json_normalize(response.json().get('news'))

    return requests.post(
        url=f"{es_url}/_bulk",
        headers={
            'Authorization': f'ApiKey {es_api_key}',
            'Content-Type': 'application/x-ndjson'
        },
        data=format_bulk_markets_news(ticker_news_series, index_suffix)
    )
