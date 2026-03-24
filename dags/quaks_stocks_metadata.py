from airflow.sdk import DAG, task
from airflow.providers.cncf.kubernetes.secret import Secret
from datetime import datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 0,
}

dag = DAG(
    "quaks_stocks_metadata",
    default_args=default_args,
    schedule="0 8 * * 1",
    catchup=False,
)


@task.kubernetes(
    image="bsantanna/java-python-dev",
    namespace="airflow",
    secrets=[Secret('env', None, 'quaks-dags-secrets')],
)
def load_stocks_metadata():
    import os
    import time
    import math
    import requests
    import json
    from datetime import datetime

    def safe_float(val):
        if val is None:
            return None
        try:
            f = float(val)
            return None if math.isnan(f) or math.isinf(f) else f
        except (ValueError, TypeError):
            return None

    def safe_int(val):
        f = safe_float(val)
        return int(f) if f is not None else None

    finnhub_request_times = []

    def finnhub_get(path, params=None):
        finnhub_api_key = os.environ.get('FINNHUB_API_KEY')
        if params is None:
            params = {}
        params['token'] = finnhub_api_key
        now = time.time()
        finnhub_request_times[:] = [t for t in finnhub_request_times if now - t < 60]
        if len(finnhub_request_times) >= 60:
            wait = 60 - (now - finnhub_request_times[0])
            if wait > 0:
                print(f"  Finnhub rate limit reached, waiting {wait:.1f}s...")
                time.sleep(wait)
        finnhub_request_times.append(time.time())
        return requests.get(f"https://finnhub.io/api/v1{path}", params=params).json()

    def format_bulk_metadata(ticker, profile, metrics, index_suffix):
        today = datetime.now().strftime('%Y-%m-%d')
        index_name = f"quaks_stocks-metadata_{index_suffix}"

        id_str = f"{ticker}_{today}"

        market_cap_millions = safe_float(profile.get('marketCapitalization'))
        market_cap = safe_int(market_cap_millions * 1_000_000) if market_cap_millions else None

        shares_millions = safe_float(profile.get('shareOutstanding'))
        shares = safe_int(shares_millions * 1_000_000) if shares_millions else None

        m = metrics.get('metric', {})

        meta = {"index": {"_index": index_name, "_id": id_str}}
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
            "ebitda": safe_int(m.get('ebitdTTM')),
            "pe_ratio": safe_float(m.get('peBasicExclExtraTTM')),
            "peg_ratio": safe_float(m.get('pegRatio')),
            "book_value": safe_float(m.get('bookValuePerShareQuarterly')),
            "dividend_per_share": safe_float(m.get('dividendPerShareAnnual')),
            "dividend_yield": safe_float(m.get('dividendYieldIndicatedAnnual')),
            "eps": safe_float(m.get('epsBasicExclExtraItemsTTM')),
            "revenue_per_share_ttm": safe_float(m.get('revenuePerShareTTM')),
            "profit_margin": safe_float(m.get('netProfitMarginTTM')),
            "operating_margin_ttm": safe_float(m.get('operatingMarginTTM')),
            "return_on_assets_ttm": safe_float(m.get('roaTTM')),
            "return_on_equity_ttm": safe_float(m.get('roeTTM')),
            "revenue_ttm": safe_int(m.get('revenueTTM')),
            "gross_profit_ttm": None,
            "diluted_eps_ttm": safe_float(m.get('epsBasicExclExtraItemsTTM')),
            "quarterly_earnings_growth_yoy": safe_float(m.get('epsGrowthQuarterlyYoy')),
            "quarterly_revenue_growth_yoy": safe_float(m.get('revenueGrowthQuarterlyYoy')),
            "analyst_target_price": safe_float(m.get('targetMedianPrice')),
            "analyst_rating_strong_buy": None,
            "analyst_rating_buy": None,
            "analyst_rating_hold": None,
            "analyst_rating_sell": None,
            "analyst_rating_strong_sell": None,
            "trailing_pe": safe_float(m.get('peBasicExclExtraTTM')),
            "forward_pe": safe_float(m.get('peExclExtraAnnual')),
            "price_to_sales_ratio_ttm": safe_float(m.get('psTTM')),
            "price_to_book_ratio": safe_float(m.get('pbQuarterly')),
            "ev_to_revenue": safe_float(m.get('enterpriseValueOverRevenueAnnual')),
            "ev_to_ebitda": safe_float(m.get('enterpriseValueOverEBITDAAnnual')),
            "beta": safe_float(m.get('beta')),
            "week_52_high": safe_float(m.get('52WeekHigh')),
            "week_52_low": safe_float(m.get('52WeekLow')),
            "moving_average_50_day": safe_float(m.get('50DayMA')),
            "moving_average_200_day": safe_float(m.get('200DayMA')),
            "shares_outstanding": shares,
            "shares_float": None,
            "percent_insiders": None,
            "percent_institutions": None,
            "dividend_date": None,
            "ex_dividend_date": None,
        }

        lines = [json.dumps(meta), json.dumps(doc)]
        return (("\n".join(lines)) + "\n").encode("utf-8")

    def ingest_metadata(ticker, index_suffix="latest"):
        es_url = os.environ.get('ELASTICSEARCH_URL')
        es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')

        profile = finnhub_get('/stock/profile2', {'symbol': ticker})
        if not profile or not profile.get('ticker'):
            print(f"  No profile data for {ticker}")
            return

        metrics = finnhub_get('/stock/metric', {'symbol': ticker, 'metric': 'all'})

        data = format_bulk_metadata(ticker, profile, metrics, index_suffix)
        resp = requests.post(
            url=f"{es_url}/_bulk",
            headers={
                'Authorization': f'ApiKey {es_api_key}',
                'Content-Type': 'application/x-ndjson'
            },
            data=data
        )
        print(f"  Metadata for {ticker}: {resp.status_code}")

    api_endpoint = "https://quaks.ai"
    indexed_key_ticker_list = requests.get(f"{api_endpoint}/json/indexed_key_ticker_list.json").json()

    for company in indexed_key_ticker_list:
        ticker = company["key_ticker"]
        index = company["index"]
        try:
            print(f"Processing metadata for {ticker}...")
            ingest_metadata(ticker, index)
        except Exception as e:
            print(f"Error processing metadata for {ticker}: {e}")
        time.sleep(0.5)


with dag:
    load_stocks_metadata()
