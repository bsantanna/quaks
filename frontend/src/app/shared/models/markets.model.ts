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
  url: string
  date: string
  source: string
  headline: string
  summary: string
  content: string
  images: NewsImage[]
  key_ticker: string[]
}

export interface NewsList {
  items: NewsItem[]
  cursor: string
}
