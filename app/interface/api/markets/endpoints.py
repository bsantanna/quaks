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
    - `start_date` (query, optional): Start of the date range in `yyyy-mm-dd` format.
    - `end_date` (query, optional): End of the date range in `yyyy-mm-dd` format.
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
    result = await markets_stats_service.get_stats_close(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=request.start_date,
        end_date=request.end_date,
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
    - `key_ticker` (query, optional): Filter by ticker symbol (e.g. `AAPL`).
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
    results, sort = await markets_news_service.get_news(
        index_name=index_name,
        id=request.id,
        key_ticker=request.key_ticker,
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
                headline=item.get("_source").get("text_headline"),
                summary=item.get("_source").get("text_summary"),
                content=item.get("_source").get("text_content"),
                date=item.get("_source").get("date_reference"),
                images=item.get("_source").get("obj_images"),
                key_ticker=item.get("_source").get("key_ticker"),
            )
        )

    return NewsList(
        items=news_items,
        cursor=sort,
    )


@router.get(
    path="/indicator/{indicator_name}/{index_name}/{key_ticker}",
    response_model=IndicatorResponse,
    operation_id="get_indicator",
    summary="Get a technical indicator for a ticker",
    description="""
    Returns technical indicator values for a ticker over a date range.

    Supported indicators:
    - `ad` — Accumulation/Distribution: measures cumulative money flow volume.
    - `adx` — Average Directional Index: measures trend strength (extra param: `period`, default 14).
    - `cci` — Commodity Channel Index: measures price deviation from mean (extra params: `period` default 20, `constant` default 0.015).
    - `ema` — Exponential Moving Average crossover (extra params: `short_window` default 12, `long_window` default 26).
    - `macd` — Moving Average Convergence/Divergence (extra params: `short_window` default 12, `long_window` default 26, `signal_window` default 9).
    - `obv` — On-Balance Volume: measures buying/selling pressure via cumulative volume.
    - `rsi` — Relative Strength Index: momentum on 0-100 scale (extra param: `period`, default 14).
    - `stoch` — Stochastic Oscillator: compares close to price range (extra params: `lookback` default 14, `smooth_k` default 3, `smooth_d` default 3).

    Parameters:
    - `indicator_name` (path): One of `ad`, `adx`, `cci`, `ema`, `macd`, `obv`, `rsi`, `stoch`.
    - `index_name` (path): The Elasticsearch index (e.g. `stocks-eod`).
    - `key_ticker` (path): The ticker symbol (e.g. `AAPL`).
    - `start_date` (query): Start of date range in `yyyy-mm-dd` format.
    - `end_date` (query): End of date range in `yyyy-mm-dd` format.
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
    base_kwargs = dict(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    if indicator_name == "ad":
        data = await markets_stats_service.get_indicator_ad(**base_kwargs)
    elif indicator_name == "adx":
        data = await markets_stats_service.get_indicator_adx(
            **base_kwargs, period=request.period or 14
        )
    elif indicator_name == "cci":
        data = await markets_stats_service.get_indicator_cci(
            **base_kwargs,
            period=request.period or 20,
            constant=request.constant or 0.015,
        )
    elif indicator_name == "ema":
        data = await markets_stats_service.get_indicator_ema(
            **base_kwargs,
            short_window=request.short_window or 12,
            long_window=request.long_window or 26,
        )
    elif indicator_name == "macd":
        data = await markets_stats_service.get_indicator_macd(
            **base_kwargs,
            short_window=request.short_window or 12,
            long_window=request.long_window or 26,
            signal_window=request.signal_window or 9,
        )
    elif indicator_name == "obv":
        data = await markets_stats_service.get_indicator_obv(**base_kwargs)
    elif indicator_name == "rsi":
        data = await markets_stats_service.get_indicator_rsi(
            **base_kwargs, period=request.period or 14
        )
    elif indicator_name == "stoch":
        data = await markets_stats_service.get_indicator_stoch(
            **base_kwargs,
            lookback=request.lookback or 14,
            smooth_k=request.smooth_k or 3,
            smooth_d=request.smooth_d or 3,
        )
    else:
        raise InvalidFieldError(
            "indicator_name",
            f"Unknown indicator '{indicator_name}'. "
            f"Supported: ad, adx, cci, ema, macd, obv, rsi, stoch",
        )

    return IndicatorResponse(
        key_ticker=key_ticker, indicator=indicator_name, data=data
    )
