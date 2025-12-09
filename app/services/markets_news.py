from elasticsearch import Elasticsearch


class MarketsNewsService:

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    async def get_markets_news_related(self, index_name: str, key_ticker: str, size=10) -> list[dict]:
        search_params = {
            "id": "get_markets_news_related_template",
            "params": {
                "key_ticker": key_ticker,
                "size": size
            }
        }

        response = self.es.search_template(index=index_name, body=search_params)
        result = []
        for hit in response['hits']['hits']:
            result.append(hit['_source'])

        return result
