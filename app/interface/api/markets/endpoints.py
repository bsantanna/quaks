import re
from datetime import datetime, timedelta
from html import unescape

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from typing_extensions import Annotated

from app.core.container import Container
from app.domain.exceptions.base import InvalidFieldError
from app.interface.api.cache_control import cache_control
from app.interface.api.markets.schema import (
    IndicatorRequest,
    IndicatorResponse,
    NewsItem,
    NewsList,
    NewsListRequest,
    StatsClose,
    StatsCloseRequest,
)
from app.services.markets_news import MarketsNewsService
from app.services.markets_stats import MarketsStatsService

router = APIRouter()

_INDEX_NAME_PATTERN = re.compile(r"^[a-z0-9\-_]+$")


def _validate_index_name(index_name: str):
    if not _INDEX_NAME_PATTERN.match(index_name):
        raise InvalidFieldError(
            "index_name",
            "Must contain only lowercase letters, numbers, hyphens, or underscores",
        )


@router.get(
    path="/stats_close/{index_name}/{key_ticker}",
    response_model=StatsClose,
    operation_id="get_stats_close",
    summary="Get close price statistics for a ticker",
    description="""
    Returns the most recent OHLCV data and percent variance for a given ticker symbol
    within an optional date range.

    This endpoint queries Elasticsearch aggregation templates to compute
    close price statistics from end-of-day market data.

    Parameters:
    - `index_name` (path): The Elasticsearch index to query (e.g. `stocks-eod`).
    - `key_ticker` (path): The ticker symbol (e.g. `AAPL`, `MSFT`).
    - `start_date` (query, optional): Start of the date range in `yyyy-mm-dd` format. Defaults to 90 days ago.
    - `end_date` (query, optional): End of the date range in `yyyy-mm-dd` format. Defaults to today.
    """,
    response_description="Close price statistics for the ticker",
    responses={
        200: {
            "description": "Successfully retrieved close price statistics",
            "content": {
                "application/json": {
                    "example": {
                        "key_ticker": "AAPL",
                        "most_recent_close": 198.11,
                        "most_recent_open": 196.50,
                        "most_recent_high": 199.62,
                        "most_recent_low": 196.00,
                        "most_recent_volume": 54132987.0,
                        "most_recent_date": "2025-01-10",
                        "percent_variance": 1.23,
                    }
                }
            },
        },
        400: {
            "description": "Invalid date format or range",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Field start_date, end_date is invalid, reason: Date must be in yyyy-mm-dd format"
                    }
                }
            },
        },
    },
    dependencies=[cache_control(3600)],
)
@inject
async def get_stats_close(
    index_name: str,
    key_ticker: str,
    markets_stats_service: Annotated[
        MarketsStatsService, Depends(Provide[Container.markets_stats_service])
    ],
    request: Annotated[StatsCloseRequest, Depends()],
):
    _validate_index_name(index_name)
    today = datetime.now()
    end_date = request.end_date or today.strftime("%Y-%m-%d")
    start_date = request.start_date or (today - timedelta(days=90)).strftime("%Y-%m-%d")
    result = await markets_stats_service.get_stats_close(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=start_date,
        end_date=end_date,
    )
    return StatsClose(
        key_ticker=key_ticker,
        most_recent_close=result.get("most_recent_close"),
        most_recent_open=result.get("most_recent_open"),
        most_recent_high=result.get("most_recent_high"),
        most_recent_low=result.get("most_recent_low"),
        most_recent_volume=result.get("most_recent_volume"),
        most_recent_date=result.get("most_recent_date"),
        percent_variance=result.get("percent_variance"),
    )


@router.get(
    path="/news/{index_name}",
    response_model=NewsList,
    operation_id="get_markets_news",
    summary="Get financial market news",
    description="""
    Returns paginated financial news headlines, summaries, and optional full content
    from the specified Elasticsearch index.

    Supports cursor-based pagination and filtering by ticker symbol or document ID.
    Use `cursor` from a previous response to fetch the next page.

    Parameters:
    - `index_name` (path): The Elasticsearch index to query (e.g. `markets-news`).
    - `size` (query): Number of news items to return per page.
    - `id` (query, optional): Filter by specific document ID.
    - `key_ticker` (query, optional): Filter by ticker symbol (e.g. `AAPL`). Takes precedence over `search_term`.
    - `search_term` (query, optional): Full-text search across headline, summary, and content fields. Ignored when `key_ticker` is provided.
    - `cursor` (query, optional): Base64-encoded pagination cursor from a previous response.
    - `include_text_content` (query, optional): Include full article text content.
    - `include_key_ticker` (query, optional): Include associated ticker symbols.
    - `include_obj_images` (query, optional): Include image objects (URLs and sizes).
    """,
    response_description="Paginated list of news items with cursor for next page",
    responses={
        200: {
            "description": "Successfully retrieved news items",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "abc123",
                                "date": "2025-01-10T14:30:00Z",
                                "source": "reuters",
                                "headline": "Tech stocks rally on strong earnings",
                                "summary": "Major tech companies reported better-than-expected Q4 earnings...",
                                "content": None,
                                "images": None,
                                "key_ticker": None,
                            },
                            {
                                "id": "def456",
                                "date": "2025-01-10T13:15:00Z",
                                "source": "bloomberg",
                                "headline": "Fed signals rate decision ahead",
                                "summary": "Federal Reserve officials indicated a cautious approach...",
                                "content": None,
                                "images": None,
                                "key_ticker": None,
                            },
                        ],
                        "cursor": "WzE3MDQ4OTAwMDBd",
                    }
                }
            },
        },
    },
    dependencies=[cache_control(3600)],
)
@inject
async def get_news(
    index_name: str,
    markets_news_service: Annotated[
        MarketsNewsService, Depends(Provide[Container.markets_news_service])
    ],
    request: Annotated[NewsListRequest, Depends()],
):
    _validate_index_name(index_name)
    results, sort = await markets_news_service.get_news(
        index_name=index_name,
        id=request.id,
        key_ticker=request.key_ticker,
        search_term=request.search_term,
        size=request.size,
        cursor=request.cursor,
        include_text_content=request.include_text_content,
        include_key_ticker=request.include_key_ticker,
        include_obj_images=request.include_obj_images,
    )

    news_items = []
    for item in results:
        news_items.append(
            NewsItem(
                id=item.get("_id"),
                source=item.get("_source").get("key_source"),
                headline=unescape(item.get("_source").get("text_headline") or ""),
                summary=unescape(item.get("_source").get("text_summary") or ""),
                content=unescape(item.get("_source").get("text_content") or ""),
                date=item.get("_source").get("date_reference"),
                images=item.get("_source").get("obj_images"),
                key_ticker=item.get("_source").get("key_ticker"),
            )
        )

    return NewsList(
        items=news_items,
        cursor=sort,
    )


# Indicator configuration: maps indicator name to its service method suffix
# and the extra query parameters it accepts with their defaults.
# All indicators share the base params: index_name, key_ticker, start_date, end_date.
INDICATOR_CONFIG = {
    "ad": {},
    "adx": {"period": 14},
    "cci": {"period": 20, "constant": 0.015},
    "ema": {"short_window": 12, "long_window": 26},
    "macd": {"short_window": 12, "long_window": 26, "signal_window": 9},
    "obv": {},
    "rsi": {"period": 14},
    "stoch": {"lookback": 14, "smooth_k": 3, "smooth_d": 3},
}

SUPPORTED_INDICATORS = ", ".join(sorted(INDICATOR_CONFIG.keys()))


@router.get(
    path="/indicator/{indicator_name}/{index_name}/{key_ticker}",
    response_model=IndicatorResponse,
    operation_id="get_indicator",
    summary="Get a technical indicator for a ticker",
    description="""
    Returns technical indicator values for a ticker over a date range.

    Dates are optional: `start_date` defaults to 90 days ago and `end_date`
    defaults to today. Each indicator accepts specific extra query parameters
    listed below; any unrelated parameters are ignored.

    **Supported indicators and their query parameters:**

    | Indicator | Description | Extra params (defaults) |
    |-----------|-------------|------------------------|
    | `ad` | Accumulation/Distribution — cumulative money flow volume | — |
    | `adx` | Average Directional Index — trend strength | `period` (14) |
    | `cci` | Commodity Channel Index — price deviation from mean | `period` (20), `constant` (0.015) |
    | `ema` | Exponential Moving Average — crossover detection | `short_window` (12), `long_window` (26) |
    | `macd` | Moving Average Convergence/Divergence — trend momentum | `short_window` (12), `long_window` (26), `signal_window` (9) |
    | `obv` | On-Balance Volume — buying/selling pressure | — |
    | `rsi` | Relative Strength Index — momentum 0-100 scale | `period` (14) |
    | `stoch` | Stochastic Oscillator — close vs price range | `lookback` (14), `smooth_k` (3), `smooth_d` (3) |

    **Path parameters:**
    - `indicator_name`: One of `ad`, `adx`, `cci`, `ema`, `macd`, `obv`, `rsi`, `stoch`.
    - `index_name`: The Elasticsearch index (e.g. `stocks-eod`).
    - `key_ticker`: The ticker symbol (e.g. `AAPL`).

    **Common query parameters:**
    - `start_date` (optional): Start of date range in `yyyy-mm-dd` format. Defaults to 90 days ago.
    - `end_date` (optional): End of date range in `yyyy-mm-dd` format. Defaults to today.
    """,
    response_description="Indicator time series data",
    responses={
        200: {
            "description": "Successfully retrieved indicator data",
            "content": {
                "application/json": {
                    "example": {
                        "key_ticker": "AAPL",
                        "indicator": "rsi",
                        "data": [{"date": "2025-01-10", "value": 62.35}],
                    }
                }
            },
        },
        400: {
            "description": "Invalid indicator name or parameter",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Field indicator_name is invalid, reason: "
                        "Unknown indicator 'xyz'. "
                        "Supported: ad, adx, cci, ema, macd, obv, rsi, stoch"
                    }
                }
            },
        },
    },
    dependencies=[cache_control(3600)],
)
@inject
async def get_indicator(
    indicator_name: str,
    index_name: str,
    key_ticker: str,
    markets_stats_service: Annotated[
        MarketsStatsService, Depends(Provide[Container.markets_stats_service])
    ],
    request: Annotated[IndicatorRequest, Depends()],
):
    _validate_index_name(index_name)

    if indicator_name not in INDICATOR_CONFIG:
        raise InvalidFieldError(
            "indicator_name",
            f"Unknown indicator '{indicator_name}'. "
            f"Supported: {SUPPORTED_INDICATORS}",
        )

    today = datetime.now()
    end_date = request.end_date or today.strftime("%Y-%m-%d")
    start_date = request.start_date or (today - timedelta(days=90)).strftime("%Y-%m-%d")

    extra_params = INDICATOR_CONFIG[indicator_name]
    kwargs = dict(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=start_date,
        end_date=end_date,
    )
    for param, default in extra_params.items():
        kwargs[param] = getattr(request, param) or default

    method = getattr(markets_stats_service, f"get_indicator_{indicator_name}")
    data = await method(**kwargs)

    return IndicatorResponse(
        key_ticker=key_ticker, indicator=indicator_name, data=data
    )
