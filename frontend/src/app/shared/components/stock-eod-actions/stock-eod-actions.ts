import {Component, effect, inject, input, PLATFORM_ID, signal, WritableSignal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {HttpClient} from '@angular/common/http';
import {forkJoin} from 'rxjs';
import {StockEodInsights} from './stock-eod-insights/stock-eod-insights';
import {StockEodTools} from './stock-eod-tools/stock-eod-tools';
import {HeatmapConstituent} from '../../models/markets.model';

@Component({
  selector: 'app-stock-eod-actions',
  imports: [
    StockEodInsights,
    StockEodTools
  ],
  templateUrl: './stock-eod-actions.html',
  styleUrl: './stock-eod-actions.scss',
})
export class StockEodActions {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly httpClient = inject(HttpClient);

  readonly selectedTab: WritableSignal<string> = signal<string>('tools');
  readonly keyTicker = input.required<string>();
  readonly isHeatmapStock = signal(false);

  constructor() {
    if (this.isBrowser) {
      effect(() => {
        const ticker = this.keyTicker();
        forkJoin({
          sp500: this.httpClient.get<HeatmapConstituent[]>('/json/heatmap_sp500.json'),
          nasdaq100: this.httpClient.get<HeatmapConstituent[]>('/json/heatmap_nasdaq100.json'),
        }).subscribe(({sp500, nasdaq100}) => {
          const allTickers = new Set([...sp500.map(c => c.ticker), ...nasdaq100.map(c => c.ticker)]);
          this.isHeatmapStock.set(allTickers.has(ticker));
        });
      });
    }
  }
}
