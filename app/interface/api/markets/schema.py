from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator
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
            "start_date, end_date", "Date must be in yyyy-mm-dd format"
        )


def _validate_date_order(start_date: Optional[str], end_date: Optional[str]):
    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        if start >= end:
            raise InvalidFieldError(
                "start_date, end_date", "Start date must be before end date"
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
    cursor: str


class NewsListRequest(BaseModel):
    size: int
    id: Optional[str] = None
    key_ticker: Optional[str] = None
    cursor: Optional[str] = None
    include_text_content: Optional[bool] = None
    include_key_ticker: Optional[bool] = None
    include_obj_images: Optional[bool] = None

    @field_validator("id", "key_ticker", "cursor")
    @classmethod
    def validate_empty_format(cls, v: str) -> Optional[str]:
        if v == "":
            return None
        return v


class StatsClose(BaseModel):
    key_ticker: str
    most_recent_close: float
    most_recent_open: float
    most_recent_high: float
    most_recent_low: float
    most_recent_volume: float
    most_recent_date: str
    percent_variance: float


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


class IndicatorADRequest(_DateRangeRequest):
    pass


class IndicatorOBVRequest(_DateRangeRequest):
    pass


class IndicatorADXRequest(_DateRangeRequest):
    period: int = 14


class IndicatorRSIRequest(_DateRangeRequest):
    period: int = 14


class IndicatorCCIRequest(_DateRangeRequest):
    period: int = 20
    constant: float = 0.015


class IndicatorEMARequest(_DateRangeRequest):
    short_window: int = 12
    long_window: int = 26


class IndicatorMACDRequest(_DateRangeRequest):
    short_window: int = 12
    long_window: int = 26
    signal_window: int = 9


class IndicatorStochRequest(_DateRangeRequest):
    lookback: int = 14
    smooth_k: int = 3
    smooth_d: int = 3


class IndicatorResponse(BaseModel):
    key_ticker: str
    indicator: str
    data: list[Any]
