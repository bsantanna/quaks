import {Component, computed, effect, inject, OnDestroy, signal, WritableSignal} from '@angular/core';
import {ActivatedRoute, ParamMap, Params} from '@angular/router';
import {toSignal} from '@angular/core/rxjs-interop';
import {DomSanitizer, SafeResourceUrl} from '@angular/platform-browser';
import {StockInfoHeader} from './stock-info-header/stock-info-header';
import {ShareUrlService} from '../services/share-url.service';
import {IndexedKeyTickerService} from '../services/indexed-key-ticker.service';
import {StockEodTools} from './stock-eod-tools/stock-eod-tools';
import {StockEodInsights} from './stock-eod-insights/stock-eod-insights';
import {DASHBOARD_IDS, IFRAME_STYLE} from '../constants';


@Component({
  selector: 'app-markets-stocks-eod-dashboard',
  imports: [StockInfoHeader, StockEodTools, StockEodInsights],
  templateUrl: './markets-stocks-eod-dashboard.html',
  styleUrl: './markets-stocks-eod-dashboard.scss',
})
export class MarketsStocksEodDashboard implements OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly shareUrlService = inject(ShareUrlService);
  private readonly indexedKeyTickerService = inject(IndexedKeyTickerService);

  private readonly paramMap = toSignal<ParamMap>(this.route.paramMap);
  private readonly queryParams = toSignal<Params>(this.route.queryParams);
  readonly keyTicker = computed(() => this.paramMap()?.get('keyTicker') ?? '');
  readonly companyName = computed(() => this.indexedKeyTickerService.findKeyTicker(this.keyTicker())?.name ?? '');
  readonly intervalInDates = computed<string>(() => this.queryParams()?.['interval'] ?? '');
  readonly intervalInDays: WritableSignal<number> = signal<number>(90);
  readonly useIntervalInDates = computed<boolean>(() => this.intervalInDates().trim().length > 0);
  readonly selectedTab: WritableSignal<string> = signal<string>('insights');
  readonly kibanaUrl = computed<SafeResourceUrl>(() => {
    const symbol = encodeURIComponent(this.keyTicker());
    const baseUrl = 'https://kibana.quaks.ai/app/dashboards';

    const dashboardId = (this.intervalInDays() > 30 || this.useIntervalInDates())
      ? DASHBOARD_IDS.stocks_eod_ohlcv_long
      : DASHBOARD_IDS.stocks_eod_ohlcv_short;

    const timeRange = this.useIntervalInDates()
      ? `time:(from:'${this.intervalInDates().split('_')[0]}',to:'${this.intervalInDates().split('_')[1]}')`
      : `time:(from:now-${this.intervalInDays()}d,to:now)`;

    const embedParams = new URLSearchParams({
      embed: 'true',
      'show-time-filter': 'false',
      'hide-filter-bar': 'true',
      '_g': `(refreshInterval:(pause:!t,value:60000),${timeRange})`,
      '_a': `(query:(language:kuery,query:'key_ticker:${symbol}'))`
    });

    const fullUrl = `${baseUrl}?auth_provider_hint=anonymous1#/view/${dashboardId}?${embedParams.toString()}`;
    return this.sanitizer.bypassSecurityTrustResourceUrl(fullUrl);
  });


  constructor() {
    effect(() => {
      const ticker = this.keyTicker();
      const dates = this.intervalInDates();

      const title = `Stock Analysis ${ticker}`;

      if (dates) {
        this.shareUrlService.update({
          title,
          url: window.location.href
        });
      } else {
        this.shareUrlService.update({
          title,
          url: `${window.location.href.split('?')[0]}?interval=${this.shareUrlService.getPastDateInDays(this.intervalInDays())}_${this.shareUrlService.getPastDateInDays(1)}`
        });
      }
    });
  }

  onIframeLoad(iframe: HTMLIFrameElement) {
    try {
      const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
      if (iframeDoc) {
        const style = iframeDoc.createElement('style');
        style.innerHTML = IFRAME_STYLE;
        iframeDoc.head.appendChild(style);
      }
    } catch (e) {
      console.error('Error injecting styles into iframe', e);
    }
  }

  ngOnDestroy(): void {
    this.shareUrlService.update({title: '', url: ''});
  }

}
