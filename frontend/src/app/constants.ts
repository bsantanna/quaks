export const DASHBOARDS_ENDPOINT = 'https://quaks.ai/dashboards/app/dashboards';

export const DASHBOARDS_IDS = {
  'stocks_eod_ohlcv': '827cced8-7899-40de-93c0-0515755f221b',
  'stocks_eod_indicator_ad': '347f6198-18f3-4a89-a139-68ccc5489691',
  'stocks_eod_indicator_adx': '35a14add-6d73-47ae-b32f-d6f893a8f674',
  'stocks_eod_indicator_cci': '0f45967e-b3d3-4ef4-8b50-46e3ff4bb69a',
  'stocks_eod_indicator_ema': '33ff269e-ace7-4d90-aeb1-976c5e76fedb',
  'stocks_eod_indicator_macd': '80c11302-00b2-4214-804e-f3662a9b7523',
  'stocks_eod_indicator_obv': '306d31a7-ed72-4a53-95d6-1620ff28ce08',
  'stocks_eod_indicator_rsi': '67cf25be-90dc-4af6-9078-5d6bd74e6622',
  'stocks_eod_indicator_stoch': '64505c35-995a-483c-91bb-084309d9454a',
}

export const IFRAME_STYLE = `
  html, body {
    overflow:hidden;
    background-color: #0B1628;
    scrollbar-width: none !important; /* Firefox */
    -ms-overflow-style: none !important;  /* IE and Edge */
  }
  html::-webkit-scrollbar, body::-webkit-scrollbar, {
    display: none !important;
  }
  .euiHorizontalRule {
    display: none !important;
  }
  .embPanel__hoverActions {
    display: none !important;
  }
  .kbnGrid {
    margin-top: 3vh;
  }
`

export const STOCK_MARKETS = [
  'nasdaq_100',
];
