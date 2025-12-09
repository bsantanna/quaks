from airflow.sdk import DAG, task
from airflow.providers.cncf.kubernetes.secret import Secret
from datetime import datetime

from app.utils.data_ingestion_utils import ingest_markets_news

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 0,
}

dag = DAG(
    "quant_agents_markets_news",
    default_args=default_args,
    schedule="0 * * * *",
    catchup=False,
)

@task.kubernetes(
    image="bsantanna/java-python-dev",
    namespace="quant-agents",
    secrets=[Secret('env', None, 'quant-agents-secrets')],
)
def load_markets_news():
    import hashlib
    import os
    import requests
    import json
    import pandas as pd
    from datetime import datetime

    def format_bulk_markets_news(df: pd.DataFrame, index_suffix: str) -> bytes:
        index_name = f"quant-agents_markets-news_{index_suffix}"
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

    def ingest_markets_news(ticker: str, limit=20, index_suffix="latest"):
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

    api_endpoint = "https://quaks.ai"
    indexed_key_ticker_list = requests.get(f"{api_endpoint}/json/indexed_key_ticker_list.json").json()

    for company in indexed_key_ticker_list:
        stocks_eod_response = ingest_markets_news(company["key_ticker"],  company["index"])
        print(f"Ingestion complete market news for {company["key_ticker"]}, index {company["index"]}: {stocks_eod_response.json()}")

with dag:
    load_markets_news()
