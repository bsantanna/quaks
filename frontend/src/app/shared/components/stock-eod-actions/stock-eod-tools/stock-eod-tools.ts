import {Component, inject, input} from '@angular/core';
import {Router} from '@angular/router';

@Component({
  selector: 'app-stock-eod-tools',
  imports: [],
  templateUrl: './stock-eod-tools.html',
  styleUrl: './stock-eod-tools.scss',
})
export class StockEodTools {

  readonly keyTicker = input.required<string>();

  private readonly router = inject(Router);
  readonly isStocksRoute = this.router.url.includes('/markets/stocks/');
  readonly isNewsRoute = this.router.url.includes('/markets/news/');
  readonly isPerformanceRoute = this.router.url.includes('/markets/performance');

}
