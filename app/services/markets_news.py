import base64
import json

from elasticsearch import Elasticsearch


class MarketsNewsService:

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    async def get_news(
            self,
            index_name: str,
            id: str = None,
            key_ticker: str = None,
            search_term: str = None,
            size=10,
            cursor: str = None,
            include_text_content=False,
            include_key_ticker=False,
            include_obj_images=False):
        params = {
            "size": size,
            "include_text_content": include_text_content,
            "include_key_ticker": include_key_ticker,
            "include_obj_images": include_obj_images,
        }
        if id:
            params["id"] = id
        if key_ticker:
            params["key_ticker"] = key_ticker
        elif search_term:
            params["search_term"] = search_term
        if cursor:
            params["search_after"] = json.loads(base64.urlsafe_b64decode(cursor).decode())
        search_params = {
            "id": "get_markets_news_template",
            "params": params,
        }

        response = self.es.search_template(index=index_name, body=search_params)
        results = []
        last_sort = None
        for hit in response['hits']['hits']:
            results.append(hit)
            last_sort = base64.urlsafe_b64encode(json.dumps(hit['sort']).encode()).decode()

        return results, last_sort
