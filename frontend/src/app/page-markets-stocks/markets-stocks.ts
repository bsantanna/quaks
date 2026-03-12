import {Component, inject} from '@angular/core';
import {SeoService, SmallScreenMessage} from '../shared';
import {StocksHeatmaps} from './stocks-heatmaps/stocks-heatmaps';

@Component({
  selector: 'app-markets-stocks',
  imports: [StocksHeatmaps, SmallScreenMessage],
  templateUrl: './markets-stocks.html',
  styleUrl: './markets-stocks.scss',
})
export class MarketsStocks {
  constructor() {
    inject(SeoService).update({
      title: 'Stocks',
      description: 'Browse US stock market data, technical indicators, and price charts for NYSE and NASDAQ listed companies.',
      path: '/markets/stocks',
    });
  }
}
