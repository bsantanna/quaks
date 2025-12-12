const INDEX_NASDAQ_100 = 'nasdaq_100';

export const STOCK_MARKETS = [
  INDEX_NASDAQ_100,
];

const DASHBOARD_ID_STOCKS_EOD_OHLCV = '827cced8-7899-40de-93c0-0515755f221b';
const DASHBOARD_ID_STOCKS_EOD_INDICATOR_EMA = '33ff269e-ace7-4d90-aeb1-976c5e76fedb';
export const DASHBOARD_IDS = {
  'stocks_eod_ohlcv': DASHBOARD_ID_STOCKS_EOD_OHLCV,
  'stocks_eod_indicator_ema': DASHBOARD_ID_STOCKS_EOD_INDICATOR_EMA,
}

export const IFRAME_STYLE = `
  html, body {
    overflow:hidden;
    background-color: #0B1628;
    scrollbar-width: none !important; /* Firefox */
    -ms-overflow-style: none !important;  /* IE and Edge */
  }
  html::-webkit-scrollbar {
    display: none !important;
  }
  .euiHorizontalRule {
    display: none !important;
  }
  .embPanel__hoverActions{
    display: none !important;
  }
  .kbnGrid {
    margin-top: 3vh;
  }
`
