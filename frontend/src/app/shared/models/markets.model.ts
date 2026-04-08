export interface IndexedKeyTicker {
  key_ticker: string;
  index: string;
  name: string;
}

export interface StatsClose {
  key_ticker: string;
  most_recent_close: number;
  most_recent_date: string;
  most_recent_low:number;
  most_recent_high:number;
  most_recent_volume:number;
  most_recent_open:number;
  percent_variance: number;
}

export interface NewsImage {
  url: string
  size: string
}

export interface NewsItem {
  id: string
  date: string
  source: string
  headline: string
  summary: string
  content: string
  images: NewsImage[]
  key_ticker?: string[]
}

export interface NewsList {
  items: NewsItem[]
  cursor: string | null
}

export interface HeatmapConstituent {
  ticker: string
  name: string
  sector: string
  industry: string
}

export interface MarketCapItem {
  key_ticker: string
  market_capitalization: number | null
}

export interface MarketCapsBulkResponse {
  items: MarketCapItem[]
}

export interface CompanyProfile {
  key_ticker: string;
  asset_type: string | null;
  name: string | null;
  description: string | null;
  cik: string | null;
  exchange: string | null;
  currency: string | null;
  country: string | null;
  sector: string | null;
  industry: string | null;
  address: string | null;
  official_site: string | null;
  fiscal_year_end: string | null;
  latest_quarter: string | null;
  market_capitalization: number | null;
  ebitda: number | null;
  pe_ratio: number | null;
  peg_ratio: number | null;
  book_value: number | null;
  dividend_per_share: number | null;
  dividend_yield: number | null;
  eps: number | null;
  revenue_per_share_ttm: number | null;
  profit_margin: number | null;
  operating_margin_ttm: number | null;
  return_on_assets_ttm: number | null;
  return_on_equity_ttm: number | null;
  revenue_ttm: number | null;
  gross_profit_ttm: number | null;
  diluted_eps_ttm: number | null;
  quarterly_earnings_growth_yoy: number | null;
  quarterly_revenue_growth_yoy: number | null;
  analyst_target_price: number | null;
  analyst_rating_strong_buy: number | null;
  analyst_rating_buy: number | null;
  analyst_rating_hold: number | null;
  analyst_rating_sell: number | null;
  analyst_rating_strong_sell: number | null;
  trailing_pe: number | null;
  forward_pe: number | null;
  price_to_sales_ratio_ttm: number | null;
  price_to_book_ratio: number | null;
  ev_to_revenue: number | null;
  ev_to_ebitda: number | null;
  beta: number | null;
  week_52_high: number | null;
  week_52_low: number | null;
  moving_average_50_day: number | null;
  moving_average_200_day: number | null;
  shares_outstanding: number | null;
  shares_float: number | null;
  percent_insiders: number | null;
  percent_institutions: number | null;
  dividend_date: string | null;
  ex_dividend_date: string | null;
}

export interface StatsCloseBulkResponse {
  items: StatsClose[]
}

export interface InsightsNewsItem {
  id: string
  date: string
  executive_summary: string
  report_html: string | null
}

export interface InsightsNewsList {
  items: InsightsNewsItem[]
  cursor: string | null
}

export type InsightsPreviewStatus = 'pending' | 'processed' | 'cancelled';

export interface InsightsPreviewItem {
  doc_id: string;
  executive_summary: string;
  report_html: string | null;
  skill_name: string;
  author_username: string;
  date_timestamp: string;
  status: InsightsPreviewStatus;
}
