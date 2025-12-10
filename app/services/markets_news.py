from elasticsearch import Elasticsearch


class MarketsNewsService:

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    async def get_news_related(
            self,
            index_name: str,
            key_ticker: str,
            size=10,
            include_key_ticker=False,
            include_images=False
    ) -> list[dict]:
        search_params = {
            "id": "get_markets_news_related_template",
            "params": {
                "key_ticker": key_ticker,
                "size": size,
                "include_key_ticker": include_key_ticker,
                "include_images": include_images
            }
        }

        response = self.es.search_template(index=index_name, body=search_params)
        results = []
        for hit in response['hits']['hits']:
            results.append(hit['_source'])

        return results
