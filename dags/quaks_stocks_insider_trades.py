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
    "quaks_stocks_insider_trades",
    default_args=default_args,
    schedule="0 7 * * *",
    catchup=False,
)


@task.kubernetes(
    image="bsantanna/java-python-dev",
    namespace="airflow",
    secrets=[Secret('env', None, 'quaks-dags-secrets')],
)
def load_stocks_insider_trades():
    import os
    import time
    import math
    import requests
    import json
    from datetime import datetime, timedelta

    def safe_float(val):
        if val is None:
            return None
        try:
            f = float(val)
            return None if math.isnan(f) or math.isinf(f) else f
        except (ValueError, TypeError):
            return None

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

    def format_bulk_insider_trades(ticker, data, index_suffix):
        index_name = f"quaks_stocks-insider-trades_{index_suffix}"
        lines = []

        for item in data:
            name = item.get('name', '')
            txn_date = item.get('transactionDate')
            txn_code = item.get('transactionCode', '')
            txn_price = safe_float(item.get('transactionPrice'))
            change = safe_float(item.get('change'))

            if not txn_date:
                continue

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

    def ingest_insider_trades(ticker, index_suffix="latest"):
        es_url = os.environ.get('ELASTICSEARCH_URL')
        es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')

        now = datetime.now()
        from_date = (now - timedelta(days=365)).strftime('%Y-%m-%d')
        to_date = now.strftime('%Y-%m-%d')

        result = finnhub_get('/stock/insider-transactions', {
            'symbol': ticker,
            'from': from_date,
            'to': to_date,
        })
        data = result.get('data', [])

        if not data:
            print(f"  No insider trades for {ticker}")
            return

        bulk_data = format_bulk_insider_trades(ticker, data, index_suffix)
        if bulk_data:
            resp = requests.post(
                url=f"{es_url}/_bulk",
                headers={
                    'Authorization': f'ApiKey {es_api_key}',
                    'Content-Type': 'application/x-ndjson'
                },
                data=bulk_data
            )
            print(f"  Insider trades for {ticker}: {resp.status_code}")

    api_endpoint = "https://quaks.ai"
    indexed_key_ticker_list = requests.get(f"{api_endpoint}/json/indexed_key_ticker_list.json").json()

    for company in indexed_key_ticker_list:
        ticker = company["key_ticker"]
        index = company["index"]
        try:
            print(f"Processing insider trades for {ticker}...")
            ingest_insider_trades(ticker, index)
        except Exception as e:
            print(f"Error processing insider trades for {ticker}: {e}")
        time.sleep(0.5)


with dag:
    load_stocks_insider_trades()
