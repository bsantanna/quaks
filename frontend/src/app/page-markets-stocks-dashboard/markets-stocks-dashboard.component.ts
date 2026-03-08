import {Component, computed, effect, inject, OnDestroy, PLATFORM_ID, signal, WritableSignal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {ActivatedRoute, ParamMap, Params} from '@angular/router';
import {toSignal} from '@angular/core/rxjs-interop';
import {StockInfoHeader, ShareUrlService, IndexedKeyTickerService, StockEodActions, SeoService} from '../shared';
import {StockEodCharts} from './stock-eod-charts/stock-eod-charts';
import {environment} from '../../environments/environment';


@Component({
  selector: 'app-markets-stocks-eod-dashboard',
  imports: [StockInfoHeader, StockEodActions, StockEodCharts],
  templateUrl: './markets-stocks-dashboard.component.html',
  styleUrl: './markets-stocks-dashboard.component.scss',
})
export class MarketsStocksDashboard implements OnDestroy {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly shareUrlService = inject(ShareUrlService);
  private readonly indexedKeyTickerService = inject(IndexedKeyTickerService);
  private readonly seoService = inject(SeoService);

  private readonly paramMap = toSignal<ParamMap>(this.route.paramMap);
  private readonly queryParams = toSignal<Params>(this.route.queryParams);
  readonly keyTicker = computed(() => this.paramMap()?.get('keyTicker') ?? '');
  readonly companyName = computed(() => this.indexedKeyTickerService.findKeyTicker(this.keyTicker())?.name ?? '');
  readonly intervalInDates = computed<string>(() => this.queryParams()?.['interval'] ?? '');
  readonly intervalInDays: WritableSignal<number> = signal<number>(90);
  readonly useIntervalInDates = computed<boolean>(() => this.intervalInDates().trim().length > 0);
  readonly isProduction = environment.production;
  private readonly routeTitle = this.route.snapshot.title ?? '';

  constructor() {
    effect(() => {
      const ticker = this.keyTicker();
      const name = this.companyName();
      const linkTitle = `${this.routeTitle} ${ticker}`;
      this.seoService.update({
        title: name ? `${ticker} - ${name} Stock Dashboard` : `${ticker} Stock Dashboard`,
        description: `Real-time stock price, technical indicators, and market data for ${name || ticker} (${ticker}).`,
        path: `/markets/stocks/${ticker}`,
      });

      if (this.isBrowser) {
        if (this.useIntervalInDates()) {
          this.shareUrlService.update({
            title: linkTitle,
            url: window.location.href
          });
        } else {
          this.shareUrlService.update({
            title: linkTitle,
            url: `${window.location.href.split('?')[0]}?interval=${this.shareUrlService.getPastDateInDays(this.intervalInDays())}_${this.shareUrlService.getPastDateInDays(1)}`
          });
        }
      }
    });
  }

  ngOnDestroy(): void {
    this.shareUrlService.update({title: '', url: ''});
    this.seoService.reset();
  }

}
