import base64
import json

from elasticsearch import Elasticsearch


class MarketsInsightsService:

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    async def get_insights_news(
            self,
            index_name: str,
            id: str = None,
            date_from: str = None,
            date_to: str = None,
            size=10,
            cursor: str = None,
            include_report_html=False):
        params = {
            "size": size,
            "include_report_html": include_report_html,
        }
        if id:
            params["id"] = id
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if cursor:
            params["search_after"] = json.loads(base64.urlsafe_b64decode(cursor).decode())
        search_params = {
            "id": "get_insights_news_template",
            "params": params,
        }

        response = self.es.search_template(index=index_name, body=search_params)
        results = []
        last_sort = None
        for hit in response['hits']['hits']:
            results.append(hit)
            last_sort = base64.urlsafe_b64encode(json.dumps(hit['sort']).encode()).decode()

        return results, last_sort
