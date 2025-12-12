const INDEX_NASDAQ_100 = 'nasdaq_100';

export const STOCK_MARKETS = [
  INDEX_NASDAQ_100,
];

const DASHBOARD_ID_STOCKS_EOD_OHLCV_LONG = '52b71b15-6c0b-4de6-ada0-a32e7efd9d95';
const DASHBOARD_ID_STOCKS_EOD_OHLCV_SHORT = '84384148-8c80-4f99-8e4d-417a3e1ff9f9';

export const DASHBOARD_IDS = {
  'stocks_eod_ohlcv_long': DASHBOARD_ID_STOCKS_EOD_OHLCV_LONG,
  'stocks_eod_ohlcv_short': DASHBOARD_ID_STOCKS_EOD_OHLCV_SHORT
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
