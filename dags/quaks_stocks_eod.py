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
    "quaks_stocks_eod",
    default_args=default_args,
    schedule="0 10,22 * * *",
    catchup=False,
)

@task.kubernetes(
    image="bsantanna/java-python-dev",
    namespace="airflow",
    secrets=[Secret('env', None, 'quaks-dags-secrets')],
)
def load_stocks_eod():
    import os
    import time
    import requests
    import json
    import pandas as pd
    from datetime import datetime

    finnhub_request_times = []

    def format_bulk_stocks_eod(ticker: str, df: pd.DataFrame, index_suffix: str) -> bytes:
        index_name = f"quaks_stocks-eod_{index_suffix}"
        lines = []

        for _, row in df.iterrows():
            date_reference = row.get('t').split('T')[0] if 'T' in str(row.get('t', '')) else str(row.get('t'))
            open_ = row.get('o')
            close = row.get('c')
            high = row.get('h')
            low = row.get('l')
            volume = row.get('v')

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

    def fetch_eod_alpaca(ticker: str, start_date: str, end_date: str):
        url = f"https://data.alpaca.markets/v2/stocks/{ticker}/bars?timeframe=1D&start={start_date}&end={end_date}&adjustment=all"
        response = requests.get(url, headers={
            "accept": "application/json",
            "APCA-API-KEY-ID": os.environ.get('APCA-API-KEY-ID'),
            "APCA-API-SECRET-KEY": os.environ.get('APCA-API-SECRET-KEY')
        })
        if response.status_code != 200 or not response.json().get('bars'):
            return None
        return pd.json_normalize(response.json().get('bars'))

    def fetch_eod_finnhub(ticker: str, start_date: str, end_date: str):
        finnhub_api_key = os.environ.get('FINNHUB_API_KEY')
        from_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        to_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
        now = time.time()
        finnhub_request_times[:] = [t for t in finnhub_request_times if now - t < 60]
        if len(finnhub_request_times) >= 60:
            wait = 60 - (now - finnhub_request_times[0])
            if wait > 0:
                print(f"  Finnhub rate limit reached, waiting {wait:.1f}s...")
                time.sleep(wait)
        finnhub_request_times.append(time.time())
        url = f"https://finnhub.io/api/v1/stock/candle?symbol={ticker}&resolution=D&from={from_ts}&to={to_ts}&token={finnhub_api_key}"
        response = requests.get(url)
        result = response.json()
        if result.get('s') != 'ok' or not result.get('c'):
            return None
        return pd.DataFrame({
            'o': result['o'],
            'c': result['c'],
            'h': result['h'],
            'l': result['l'],
            'v': result['v'],
            't': [datetime.fromtimestamp(ts).strftime('%Y-%m-%d') for ts in result['t']],
        })

    def ingest_stocks_eod(ticker: str, index_suffix="latest") -> requests.Response:
        es_url = os.environ.get('ELASTICSEARCH_URL')
        es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')

        now = datetime.now()
        end = now.replace(day=now.day - 1)
        start = now.replace(year=now.year - 1)
        start_date = start.strftime('%Y-%m-%d')
        end_date = end.strftime('%Y-%m-%d')

        ticker_daily_time_series = fetch_eod_alpaca(ticker, start_date, end_date)
        if ticker_daily_time_series is None:
            print(f"Alpaca failed for {ticker}, trying Finnhub fallback...")
            ticker_daily_time_series = fetch_eod_finnhub(ticker, start_date, end_date)

        if ticker_daily_time_series is None:
            print(f"No EOD data available for {ticker} from either source")
            return requests.post(
                url=f"{es_url}/_bulk",
                headers={
                    'Authorization': f'ApiKey {es_api_key}',
                    'Content-Type': 'application/x-ndjson'
                },
                data=b"\n"
            )

        return requests.post(
            url=f"{es_url}/_bulk",
            headers={
                'Authorization': f'ApiKey {es_api_key}',
                'Content-Type': 'application/x-ndjson'
            },
            data=format_bulk_stocks_eod(ticker, ticker_daily_time_series, index_suffix)
        )

    api_endpoint = "https://quaks.ai"
    indexed_key_ticker_list = requests.get(f"{api_endpoint}/json/indexed_key_ticker_list.json").json()

    for company in indexed_key_ticker_list:
        stocks_eod_response = ingest_stocks_eod(company["key_ticker"], company["index"])
        print(f"Ingestion complete stocks EOD for {company['key_ticker']}, index {company['index']}: {stocks_eod_response.json()}")

with dag:
    load_stocks_eod()
