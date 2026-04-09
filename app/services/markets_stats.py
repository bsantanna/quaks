from typing_extensions import Optional
from elasticsearch import Elasticsearch


class MarketsStatsService:

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    def get_company_profile(
            self,
            index_name: str,
            key_ticker: str,
    ) -> dict:
        search_params = {
            "id": "get_metadata_profile_template",
            "params": {
                "key_ticker": key_ticker,
            }
        }

        response = self.es.search_template(index=index_name, body=search_params)
        hits = response['hits']['hits']
        if not hits:
            return {}
        return hits[0]['_source']

    def get_market_caps_bulk(
            self,
            index_name: str,
            key_tickers: list[str],
    ) -> list[dict]:
        search_params = {
            "id": "get_metadata_market_caps_template",
            "params": {
                "key_tickers": key_tickers,
                "size": len(key_tickers),
            }
        }

        response = self.es.search_template(index=index_name, body=search_params)
        buckets = response['aggregations']['by_ticker']['buckets']
        results = []
        for bucket in buckets:
            hits = bucket['latest']['hits']['hits']
            if hits:
                market_cap = hits[0]['_source'].get('market_capitalization')
                results.append({
                    'key_ticker': bucket['key'],
                    'market_capitalization': market_cap,
                })
        return results

    def get_stats_close_bulk(
            self,
            index_name: str,
            key_tickers: list[str],
            start_date: str,
            end_date: str,
    ) -> list[dict]:
        search_params = {
            "id": "get_stats_close_bulk_template",
            "params": {
                "key_tickers": key_tickers,
                "date_gte": start_date,
                "date_lte": end_date,
                "size": len(key_tickers),
            }
        }

        response = self.es.search_template(index=index_name, body=search_params)
        buckets = response['aggregations']['by_ticker']['buckets']
        results = []
        for bucket in buckets:
            stats = bucket['recent_stats']['value']
            if stats is not None:
                stats['key_ticker'] = bucket['key']
                results.append(stats)
        return results

    def get_stats_close(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: Optional[str]
    ) -> dict:
        search_params = {
            "id": "get_stats_close_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
            }
        }

        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['recent_stats']['value']

    def get_indicator_ad(self, index_name: str, key_ticker: str, start_date: str, end_date: str) -> list[dict]:
        search_params = {
            "id": "get_eod_indicator_ad_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['ad_stats']['value']

    def get_indicator_adx(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            period: int
    ) -> list[dict]:
        search_params = {
            "id": "get_eod_indicator_adx_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "period": period,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['adx_stats']['value']

    def get_indicator_cci(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            period: int,
            constant: float
    ) -> list[dict]:
        search_params = {
            "id": "get_eod_indicator_cci_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "period": period,
                "constant": constant,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['cci_stats']['value']

    def get_indicator_ema(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            short_window: int,
            long_window: int
    ) -> list[dict]:
        search_params = {
            "id": "get_eod_indicator_ema_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "short_window": short_window,
                "long_window": long_window,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['ema_stats']['value']

    def get_indicator_macd(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            short_window: int,
            long_window: int,
            signal_window: int
    ) -> list[dict]:
        search_params = {
            "id": "get_eod_indicator_macd_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "short_window": short_window,
                "long_window": long_window,
                "signal_window": signal_window,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['macd_stats']['value']

    def get_indicator_obv(self, index_name: str, key_ticker: str, start_date: str, end_date: str) -> list[dict]:
        search_params = {
            "id": "get_eod_indicator_obv_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['obv_stats']['value']

    def get_indicator_rsi(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            period: int
    ) -> list[dict]:
        search_params = {
            "id": "get_eod_indicator_rsi_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "period": period,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['rsi_stats']['value']

    def get_indicator_stoch(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            lookback: int,
            smooth_k: int,
            smooth_d: int
    ) -> list[dict]:
        search_params = {
            "id": "get_eod_indicator_stoch_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "lookback": lookback,
                "smooth_k": smooth_k,
                "smooth_d": smooth_d,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['stoch_stats']['value']
