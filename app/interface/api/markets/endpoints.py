from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from typing_extensions import Annotated

from app.core.container import Container
from app.interface.api.cache_control import cache_control
from app.interface.api.markets.schema import (
    IndicatorADRequest,
    IndicatorADXRequest,
    IndicatorCCIRequest,
    IndicatorEMARequest,
    IndicatorMACDRequest,
    IndicatorOBVRequest,
    IndicatorResponse,
    IndicatorRSIRequest,
    IndicatorStochRequest,
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
    path="/indicator/ad/{index_name}/{key_ticker}",
    response_model=IndicatorResponse,
    operation_id="get_indicator_ad",
    summary="Get Accumulation/Distribution (A/D) indicator",
    description="""
    Returns the Accumulation/Distribution indicator values for a ticker over a date range.

    The A/D indicator measures cumulative money flow volume to assess whether a stock
    is being accumulated (bought) or distributed (sold).

    Parameters:
    - `index_name` (path): The Elasticsearch index (e.g. `stocks-eod`).
    - `key_ticker` (path): The ticker symbol (e.g. `AAPL`).
    - `start_date` (query): Start of date range in `yyyy-mm-dd` format.
    - `end_date` (query): End of date range in `yyyy-mm-dd` format.
    """,
    response_description="A/D indicator time series data",
    responses={
        200: {
            "description": "Successfully retrieved A/D indicator data",
            "content": {
                "application/json": {
                    "example": {
                        "key_ticker": "AAPL",
                        "indicator": "ad",
                        "data": [{"date": "2025-01-10", "value": 1523456.78}],
                    }
                }
            },
        },
    },
    dependencies=[cache_control(3600)],
)
@inject
async def get_indicator_ad(
    index_name: str,
    key_ticker: str,
    markets_stats_service: Annotated[
        MarketsStatsService, Depends(Provide[Container.markets_stats_service])
    ],
    request: Annotated[IndicatorADRequest, Depends()],
):
    data = await markets_stats_service.get_indicator_ad(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return IndicatorResponse(key_ticker=key_ticker, indicator="ad", data=data)


@router.get(
    path="/indicator/adx/{index_name}/{key_ticker}",
    response_model=IndicatorResponse,
    operation_id="get_indicator_adx",
    summary="Get Average Directional Index (ADX) indicator",
    description="""
    Returns the ADX indicator values for a ticker over a date range.

    ADX measures trend strength regardless of direction. Values above 25 indicate
    a strong trend, while values below 20 suggest a weak or absent trend.

    Parameters:
    - `index_name` (path): The Elasticsearch index (e.g. `stocks-eod`).
    - `key_ticker` (path): The ticker symbol (e.g. `AAPL`).
    - `start_date` (query): Start of date range in `yyyy-mm-dd` format.
    - `end_date` (query): End of date range in `yyyy-mm-dd` format.
    - `period` (query): Lookback period for ADX calculation (default: 14).
    """,
    response_description="ADX indicator time series data",
    responses={
        200: {
            "description": "Successfully retrieved ADX indicator data",
            "content": {
                "application/json": {
                    "example": {
                        "key_ticker": "AAPL",
                        "indicator": "adx",
                        "data": [{"date": "2025-01-10", "value": 28.45}],
                    }
                }
            },
        },
    },
    dependencies=[cache_control(3600)],
)
@inject
async def get_indicator_adx(
    index_name: str,
    key_ticker: str,
    markets_stats_service: Annotated[
        MarketsStatsService, Depends(Provide[Container.markets_stats_service])
    ],
    request: Annotated[IndicatorADXRequest, Depends()],
):
    data = await markets_stats_service.get_indicator_adx(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=request.start_date,
        end_date=request.end_date,
        period=request.period,
    )
    return IndicatorResponse(key_ticker=key_ticker, indicator="adx", data=data)


@router.get(
    path="/indicator/cci/{index_name}/{key_ticker}",
    response_model=IndicatorResponse,
    operation_id="get_indicator_cci",
    summary="Get Commodity Channel Index (CCI) indicator",
    description="""
    Returns the CCI indicator values for a ticker over a date range.

    CCI measures a security's price deviation from its statistical mean.
    Values above +100 may indicate overbought conditions, below -100 oversold.

    Parameters:
    - `index_name` (path): The Elasticsearch index (e.g. `stocks-eod`).
    - `key_ticker` (path): The ticker symbol (e.g. `AAPL`).
    - `start_date` (query): Start of date range in `yyyy-mm-dd` format.
    - `end_date` (query): End of date range in `yyyy-mm-dd` format.
    - `period` (query): Lookback period (default: 20).
    - `constant` (query): CCI constant multiplier (default: 0.015).
    """,
    response_description="CCI indicator time series data",
    responses={
        200: {
            "description": "Successfully retrieved CCI indicator data",
            "content": {
                "application/json": {
                    "example": {
                        "key_ticker": "AAPL",
                        "indicator": "cci",
                        "data": [{"date": "2025-01-10", "value": 85.32}],
                    }
                }
            },
        },
    },
    dependencies=[cache_control(3600)],
)
@inject
async def get_indicator_cci(
    index_name: str,
    key_ticker: str,
    markets_stats_service: Annotated[
        MarketsStatsService, Depends(Provide[Container.markets_stats_service])
    ],
    request: Annotated[IndicatorCCIRequest, Depends()],
):
    data = await markets_stats_service.get_indicator_cci(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=request.start_date,
        end_date=request.end_date,
        period=request.period,
        constant=request.constant,
    )
    return IndicatorResponse(key_ticker=key_ticker, indicator="cci", data=data)


@router.get(
    path="/indicator/ema/{index_name}/{key_ticker}",
    response_model=IndicatorResponse,
    operation_id="get_indicator_ema",
    summary="Get Exponential Moving Average (EMA) indicator",
    description="""
    Returns EMA crossover data for a ticker over a date range.

    Computes short-window and long-window exponential moving averages.
    EMA crossovers are used to identify trend changes and momentum shifts.

    Parameters:
    - `index_name` (path): The Elasticsearch index (e.g. `stocks-eod`).
    - `key_ticker` (path): The ticker symbol (e.g. `AAPL`).
    - `start_date` (query): Start of date range in `yyyy-mm-dd` format.
    - `end_date` (query): End of date range in `yyyy-mm-dd` format.
    - `short_window` (query): Short EMA period (default: 12).
    - `long_window` (query): Long EMA period (default: 26).
    """,
    response_description="EMA indicator time series data",
    responses={
        200: {
            "description": "Successfully retrieved EMA indicator data",
            "content": {
                "application/json": {
                    "example": {
                        "key_ticker": "AAPL",
                        "indicator": "ema",
                        "data": [
                            {
                                "date": "2025-01-10",
                                "short_ema": 195.40,
                                "long_ema": 192.80,
                            }
                        ],
                    }
                }
            },
        },
    },
    dependencies=[cache_control(3600)],
)
@inject
async def get_indicator_ema(
    index_name: str,
    key_ticker: str,
    markets_stats_service: Annotated[
        MarketsStatsService, Depends(Provide[Container.markets_stats_service])
    ],
    request: Annotated[IndicatorEMARequest, Depends()],
):
    data = await markets_stats_service.get_indicator_ema(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=request.start_date,
        end_date=request.end_date,
        short_window=request.short_window,
        long_window=request.long_window,
    )
    return IndicatorResponse(key_ticker=key_ticker, indicator="ema", data=data)


@router.get(
    path="/indicator/macd/{index_name}/{key_ticker}",
    response_model=IndicatorResponse,
    operation_id="get_indicator_macd",
    summary="Get MACD indicator",
    description="""
    Returns Moving Average Convergence/Divergence (MACD) data for a ticker.

    MACD is a trend-following momentum indicator showing the relationship between
    two EMAs. Includes signal line for crossover detection.

    Parameters:
    - `index_name` (path): The Elasticsearch index (e.g. `stocks-eod`).
    - `key_ticker` (path): The ticker symbol (e.g. `AAPL`).
    - `start_date` (query): Start of date range in `yyyy-mm-dd` format.
    - `end_date` (query): End of date range in `yyyy-mm-dd` format.
    - `short_window` (query): Fast EMA period (default: 12).
    - `long_window` (query): Slow EMA period (default: 26).
    - `signal_window` (query): Signal line EMA period (default: 9).
    """,
    response_description="MACD indicator time series data",
    responses={
        200: {
            "description": "Successfully retrieved MACD indicator data",
            "content": {
                "application/json": {
                    "example": {
                        "key_ticker": "AAPL",
                        "indicator": "macd",
                        "data": [
                            {
                                "date": "2025-01-10",
                                "macd": 2.60,
                                "signal": 2.15,
                                "histogram": 0.45,
                            }
                        ],
                    }
                }
            },
        },
    },
    dependencies=[cache_control(3600)],
)
@inject
async def get_indicator_macd(
    index_name: str,
    key_ticker: str,
    markets_stats_service: Annotated[
        MarketsStatsService, Depends(Provide[Container.markets_stats_service])
    ],
    request: Annotated[IndicatorMACDRequest, Depends()],
):
    data = await markets_stats_service.get_indicator_macd(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=request.start_date,
        end_date=request.end_date,
        short_window=request.short_window,
        long_window=request.long_window,
        signal_window=request.signal_window,
    )
    return IndicatorResponse(key_ticker=key_ticker, indicator="macd", data=data)


@router.get(
    path="/indicator/obv/{index_name}/{key_ticker}",
    response_model=IndicatorResponse,
    operation_id="get_indicator_obv",
    summary="Get On-Balance Volume (OBV) indicator",
    description="""
    Returns the OBV indicator values for a ticker over a date range.

    OBV uses cumulative volume to measure buying and selling pressure.
    Rising OBV confirms an uptrend, while falling OBV confirms a downtrend.

    Parameters:
    - `index_name` (path): The Elasticsearch index (e.g. `stocks-eod`).
    - `key_ticker` (path): The ticker symbol (e.g. `AAPL`).
    - `start_date` (query): Start of date range in `yyyy-mm-dd` format.
    - `end_date` (query): End of date range in `yyyy-mm-dd` format.
    """,
    response_description="OBV indicator time series data",
    responses={
        200: {
            "description": "Successfully retrieved OBV indicator data",
            "content": {
                "application/json": {
                    "example": {
                        "key_ticker": "AAPL",
                        "indicator": "obv",
                        "data": [{"date": "2025-01-10", "value": 87654321.0}],
                    }
                }
            },
        },
    },
    dependencies=[cache_control(3600)],
)
@inject
async def get_indicator_obv(
    index_name: str,
    key_ticker: str,
    markets_stats_service: Annotated[
        MarketsStatsService, Depends(Provide[Container.markets_stats_service])
    ],
    request: Annotated[IndicatorOBVRequest, Depends()],
):
    data = await markets_stats_service.get_indicator_obv(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return IndicatorResponse(key_ticker=key_ticker, indicator="obv", data=data)


@router.get(
    path="/indicator/rsi/{index_name}/{key_ticker}",
    response_model=IndicatorResponse,
    operation_id="get_indicator_rsi",
    summary="Get Relative Strength Index (RSI) indicator",
    description="""
    Returns the RSI indicator values for a ticker over a date range.

    RSI measures the speed and magnitude of price changes on a 0-100 scale.
    Values above 70 typically indicate overbought conditions, below 30 oversold.

    Parameters:
    - `index_name` (path): The Elasticsearch index (e.g. `stocks-eod`).
    - `key_ticker` (path): The ticker symbol (e.g. `AAPL`).
    - `start_date` (query): Start of date range in `yyyy-mm-dd` format.
    - `end_date` (query): End of date range in `yyyy-mm-dd` format.
    - `period` (query): RSI lookback period (default: 14).
    """,
    response_description="RSI indicator time series data",
    responses={
        200: {
            "description": "Successfully retrieved RSI indicator data",
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
async def get_indicator_rsi(
    index_name: str,
    key_ticker: str,
    markets_stats_service: Annotated[
        MarketsStatsService, Depends(Provide[Container.markets_stats_service])
    ],
    request: Annotated[IndicatorRSIRequest, Depends()],
):
    data = await markets_stats_service.get_indicator_rsi(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=request.start_date,
        end_date=request.end_date,
        period=request.period,
    )
    return IndicatorResponse(key_ticker=key_ticker, indicator="rsi", data=data)


@router.get(
    path="/indicator/stoch/{index_name}/{key_ticker}",
    response_model=IndicatorResponse,
    operation_id="get_indicator_stoch",
    summary="Get Stochastic Oscillator indicator",
    description="""
    Returns Stochastic Oscillator values (%K and %D) for a ticker over a date range.

    The Stochastic Oscillator compares a closing price to its price range over a
    given period. Values above 80 suggest overbought, below 20 suggest oversold.

    Parameters:
    - `index_name` (path): The Elasticsearch index (e.g. `stocks-eod`).
    - `key_ticker` (path): The ticker symbol (e.g. `AAPL`).
    - `start_date` (query): Start of date range in `yyyy-mm-dd` format.
    - `end_date` (query): End of date range in `yyyy-mm-dd` format.
    - `lookback` (query): Lookback period for %K calculation (default: 14).
    - `smooth_k` (query): Smoothing period for %K (default: 3).
    - `smooth_d` (query): Smoothing period for %D signal line (default: 3).
    """,
    response_description="Stochastic Oscillator time series data",
    responses={
        200: {
            "description": "Successfully retrieved Stochastic Oscillator data",
            "content": {
                "application/json": {
                    "example": {
                        "key_ticker": "AAPL",
                        "indicator": "stoch",
                        "data": [
                            {"date": "2025-01-10", "percent_k": 72.5, "percent_d": 68.3}
                        ],
                    }
                }
            },
        },
    },
    dependencies=[cache_control(3600)],
)
@inject
async def get_indicator_stoch(
    index_name: str,
    key_ticker: str,
    markets_stats_service: Annotated[
        MarketsStatsService, Depends(Provide[Container.markets_stats_service])
    ],
    request: Annotated[IndicatorStochRequest, Depends()],
):
    data = await markets_stats_service.get_indicator_stoch(
        index_name=index_name,
        key_ticker=key_ticker,
        start_date=request.start_date,
        end_date=request.end_date,
        lookback=request.lookback,
        smooth_k=request.smooth_k,
        smooth_d=request.smooth_d,
    )
    return IndicatorResponse(key_ticker=key_ticker, indicator="stoch", data=data)
