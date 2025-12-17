from datetime import datetime
from typing_extensions import Optional
from pydantic import BaseModel, field_validator, model_validator
from app.domain.exceptions.base import InvalidFieldError


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
    key_ticker:Optional[str] = None
    cursor: Optional[str] = None
    include_text_content: Optional[bool] = None
    include_key_ticker: Optional[bool] = None
    include_obj_images: Optional[bool] = None

    @field_validator('cursor')
    @classmethod
    def validate_cursor_format(cls, v: str) -> Optional[str]:
        if v == '':
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

    @field_validator('end_date', 'start_date')
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        try:
            # Validate the date format
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise InvalidFieldError('start_date, end_date', 'Date must be in yyyy-mm-dd format')

    @model_validator(mode='after')
    def validate_dates_order(self):
        if self.start_date and self.end_date:
            start = datetime.strptime(self.start_date, '%Y-%m-%d')
            end = datetime.strptime(self.end_date, '%Y-%m-%d')
            if start >= end:
                raise InvalidFieldError('start_date, end_date', 'Start date must be before end date')
        return self

