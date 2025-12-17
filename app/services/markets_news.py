import base64
import json
from elasticsearch import Elasticsearch


class MarketsNewsService:

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    async def get_news(
            self,
            index_name: str,
            key_ticker: str = None,
            size=10,
            cursor: str = None,
            include_text_content=False,
            include_key_ticker=False,
            include_obj_images=False):
        search_params = {
            "id": "get_markets_news_template",
            "params": {
                "key_ticker": key_ticker,
                "size": size,
                "include_text_content": include_text_content,
                "include_key_ticker": include_key_ticker,
                "include_obj_images": include_obj_images,
                "search_after": json.loads(base64.urlsafe_b64decode(cursor).decode()) if cursor else None,
            }
        }

        response = self.es.search_template(index=index_name, body=search_params)
        results = []
        cursor = ""
        for hit in response['hits']['hits']:
            results.append(hit)
            cursor = base64.urlsafe_b64encode(json.dumps(hit['sort']).encode()).decode()

        return results, cursor
