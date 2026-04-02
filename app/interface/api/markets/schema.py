from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Any, Optional

from app.domain.exceptions.base import InvalidFieldError


def _validate_date_format(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    try:
        datetime.strptime(v, "%Y-%m-%d")
        return v
    except ValueError:
        raise InvalidFieldError(
            "date", "Date must be in yyyy-mm-dd format"
        )


def _validate_date_order(start_date: Optional[str], end_date: Optional[str]):
    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        if start >= end:
            raise InvalidFieldError(
                "date range", "Start date must be before end date"
            )


class NewsImage(BaseModel):
    url: str
    size: str


class NewsItem(BaseModel):
    id: str
    date: str
    source: str
    headline: str
    summary: str
    content: Optional[str]
    images: Optional[list[NewsImage]]
    key_ticker: Optional[list[str]]


class NewsList(BaseModel):
    items: list[NewsItem]
    cursor: Optional[str] = None


class NewsListRequest(BaseModel):
    size: int = Field(ge=1, le=15)
    id: Optional[str] = None
    key_ticker: Optional[str] = None
    search_term: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    cursor: Optional[str] = None
    include_text_content: Optional[bool] = None
    include_key_ticker: Optional[bool] = None
    include_obj_images: Optional[bool] = None

    @field_validator("id", "key_ticker", "search_term", "cursor")
    @classmethod
    def validate_empty_format(cls, v: str) -> Optional[str]:
        if v == "":
            return None
        return v

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        return _validate_date_format(v)


class InsightsNewsItem(BaseModel):
    id: str
    date: str
    executive_summary: str
    report_html: Optional[str]


class InsightsNewsList(BaseModel):
    items: list[InsightsNewsItem]
    cursor: Optional[str] = None


class InsightsNewsListRequest(BaseModel):
    size: int = Field(ge=1, le=15)
    id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    cursor: Optional[str] = None
    include_report_html: Optional[bool] = None

    @field_validator("id", "cursor")
    @classmethod
    def validate_empty_format(cls, v: str) -> Optional[str]:
        if v == "":
            return None
        return v

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        return _validate_date_format(v)


class CompanyProfile(BaseModel):
    key_ticker: str
    asset_type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    cik: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    official_site: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    latest_quarter: Optional[str] = None
    market_capitalization: Optional[int] = None
    ebitda: Optional[float] = None
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    book_value: Optional[float] = None
    dividend_per_share: Optional[float] = None
    dividend_yield: Optional[float] = None
    eps: Optional[float] = None
    revenue_per_share_ttm: Optional[float] = None
    profit_margin: Optional[float] = None
    operating_margin_ttm: Optional[float] = None
    return_on_assets_ttm: Optional[float] = None
    return_on_equity_ttm: Optional[float] = None
    revenue_ttm: Optional[int] = None
    gross_profit_ttm: Optional[int] = None
    diluted_eps_ttm: Optional[float] = None
    quarterly_earnings_growth_yoy: Optional[float] = None
    quarterly_revenue_growth_yoy: Optional[float] = None
    analyst_target_price: Optional[float] = None
    analyst_rating_strong_buy: Optional[int] = None
    analyst_rating_buy: Optional[int] = None
    analyst_rating_hold: Optional[int] = None
    analyst_rating_sell: Optional[int] = None
    analyst_rating_strong_sell: Optional[int] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_sales_ratio_ttm: Optional[float] = None
    price_to_book_ratio: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    beta: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    moving_average_50_day: Optional[float] = None
    moving_average_200_day: Optional[float] = None
    shares_outstanding: Optional[int] = None
    shares_float: Optional[int] = None
    percent_insiders: Optional[float] = None
    percent_institutions: Optional[float] = None
    dividend_date: Optional[str] = None
    ex_dividend_date: Optional[str] = None


class StatsClose(BaseModel):
    key_ticker: str
    most_recent_close: float
    most_recent_open: float
    most_recent_high: float
    most_recent_low: float
    most_recent_volume: float
    most_recent_date: str
    percent_variance: float


class StatsCloseBulkRequest(BaseModel):
    key_tickers: list[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        return _validate_date_format(v)

    @model_validator(mode="after")
    def validate_dates_order(self):
        _validate_date_order(self.start_date, self.end_date)
        return self


class StatsCloseBulkResponse(BaseModel):
    items: list[StatsClose]


class MarketCapItem(BaseModel):
    key_ticker: str
    market_capitalization: Optional[int] = None


class MarketCapsBulkRequest(BaseModel):
    key_tickers: list[str]


class MarketCapsBulkResponse(BaseModel):
    items: list[MarketCapItem]


class StatsCloseRequest(BaseModel):
    end_date: Optional[str] = None
    start_date: Optional[str] = None

    @field_validator("end_date", "start_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        return _validate_date_format(v)

    @model_validator(mode="after")
    def validate_dates_order(self):
        _validate_date_order(self.start_date, self.end_date)
        return self


# -- Indicator request models --


class _DateRangeRequest(BaseModel):
    start_date: str
    end_date: str

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        result = _validate_date_format(v)
        if result is None:
            raise InvalidFieldError("start_date, end_date", "Date is required")
        return result

    @model_validator(mode="after")
    def validate_dates_order(self):
        _validate_date_order(self.start_date, self.end_date)
        return self


class IndicatorRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period: Optional[int] = None
    constant: Optional[float] = None
    short_window: Optional[int] = None
    long_window: Optional[int] = None
    signal_window: Optional[int] = None
    lookback: Optional[int] = None
    smooth_k: Optional[int] = None
    smooth_d: Optional[int] = None

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        return _validate_date_format(v)

    @model_validator(mode="after")
    def validate_dates_order(self):
        _validate_date_order(self.start_date, self.end_date)
        return self


class IndicatorResponse(BaseModel):
    key_ticker: str
    indicator: str
    data: list[Any]


class McpNewsRequest(BaseModel):
    search_term: Optional[str] = None
    key_ticker: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    cursor: Optional[str] = None
    size: int = Field(default=3, ge=1, le=15)

    @field_validator("search_term", "key_ticker", "cursor")
    @classmethod
    def validate_empty_format(cls, v: str) -> Optional[str]:
        if v == "":
            return None
        return v

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        return _validate_date_format(v)

    @model_validator(mode="after")
    def validate_dates_order(self):
        _validate_date_order(self.date_from, self.date_to)
        return self


class McpNewsItem(BaseModel):
    headline: str
    summary: str
    content: str
    source: str
    date: str
    tickers: Optional[list[str]] = None


class McpNewsList(BaseModel):
    items: list[McpNewsItem]
    cursor: Optional[str] = None


class McpInsightsNewsRequest(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    cursor: Optional[str] = None
    size: int = Field(default=3, ge=1, le=15)
    include_report_html: bool = False

    @field_validator("cursor")
    @classmethod
    def validate_empty_format(cls, v: str) -> Optional[str]:
        if v == "":
            return None
        return v

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        return _validate_date_format(v)

    @model_validator(mode="after")
    def validate_dates_order(self):
        _validate_date_order(self.date_from, self.date_to)
        return self


class McpInsightsNewsItem(BaseModel):
    date: str
    executive_summary: str
    report_html: Optional[str] = None


class McpInsightsNewsList(BaseModel):
    items: list[McpInsightsNewsItem]
    cursor: Optional[str] = None
