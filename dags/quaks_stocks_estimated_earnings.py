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
    "quaks_stocks_estimated_earnings",
    default_args=default_args,
    schedule="0 9 * * 1",
    catchup=False,
)

@task.kubernetes(
    image="bsantanna/java-python-dev",
    namespace="airflow",
    secrets=[Secret('env', None, 'quaks-dags-secrets')],
)
def load_stocks_estimated_earnings():
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

    def map_frequency(freq):
        if freq == "quarterly":
            return "3month"
        elif freq == "annual":
            return "12month"
        return freq

    def format_bulk_estimated_earnings(ticker, eps_data, revenue_data, index_suffix):
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

            id_str = f"{ticker}_{date}_{freq}"

            meta = {"index": {"_index": index_name, "_id": id_str}}
            doc = {
                "key_ticker": ticker,
                "date": date,
                "horizon": map_frequency(freq),
                "eps_estimate_average": safe_float(item.get('epsAvg')),
                "eps_estimate_high": safe_float(item.get('epsHigh')),
                "eps_estimate_low": safe_float(item.get('epsLow')),
                "eps_estimate_analyst_count": safe_int(item.get('numberAnalysts')),
                "eps_estimate_average_7_days_ago": None,
                "eps_estimate_average_30_days_ago": None,
                "eps_estimate_average_60_days_ago": None,
                "eps_estimate_average_90_days_ago": None,
                "eps_estimate_revision_up_trailing_7_days": None,
                "eps_estimate_revision_down_trailing_7_days": None,
                "eps_estimate_revision_up_trailing_30_days": None,
                "eps_estimate_revision_down_trailing_30_days": None,
                "revenue_estimate_average": safe_float(revenue_item.get('revenueAvg')),
                "revenue_estimate_high": safe_float(revenue_item.get('revenueHigh')),
                "revenue_estimate_low": safe_float(revenue_item.get('revenueLow')),
                "revenue_estimate_analyst_count": safe_int(revenue_item.get('numberAnalysts')),
            }

            lines.append(json.dumps(meta))
            lines.append(json.dumps(doc))

        return (("\n".join(lines)) + "\n").encode("utf-8") if lines else b""

    def ingest_estimated_earnings(ticker, index_suffix="latest"):
        es_url = os.environ.get('ELASTICSEARCH_URL')
        es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')

        eps_data = finnhub_get('/stock/eps-estimate', {'symbol': ticker}).get('data', [])
        revenue_data = finnhub_get('/stock/revenue-estimate', {'symbol': ticker}).get('data', [])

        if not eps_data and not revenue_data:
            print(f"  No earnings estimates for {ticker}")
            return

        data = format_bulk_estimated_earnings(ticker, eps_data, revenue_data, index_suffix)
        if data:
            resp = requests.post(
                url=f"{es_url}/_bulk",
                headers={
                    'Authorization': f'ApiKey {es_api_key}',
                    'Content-Type': 'application/x-ndjson'
                },
                data=data
            )
            print(f"  Estimated earnings for {ticker}: {resp.status_code}")

    api_endpoint = "https://quaks.ai"
    indexed_key_ticker_list = requests.get(f"{api_endpoint}/json/indexed_key_ticker_list.json").json()

    for company in indexed_key_ticker_list:
        ticker = company["key_ticker"]
        index = company["index"]
        try:
            print(f"Processing estimated earnings for {ticker}...")
            ingest_estimated_earnings(ticker, index)
        except Exception as e:
            print(f"Error processing estimated earnings for {ticker}: {e}")
        time.sleep(0.5)

with dag:
    load_stocks_estimated_earnings()
