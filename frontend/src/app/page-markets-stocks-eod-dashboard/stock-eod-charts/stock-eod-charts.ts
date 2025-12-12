import {Component, computed, effect, inject, input, model, signal, WritableSignal} from '@angular/core';
import {DomSanitizer, SafeResourceUrl} from '@angular/platform-browser';
import {DASHBOARD_IDS, IFRAME_STYLE} from '../../constants';

@Component({
  selector: 'app-stock-eod-charts',
  imports: [],
  templateUrl: './stock-eod-charts.html',
  styleUrl: './stock-eod-charts.scss',
})
export class StockEodCharts {

  private readonly sanitizer = inject(DomSanitizer);

  readonly keyTicker = input.required<string>();
  readonly intervalInDates = input.required<string>();
  readonly useIntervalInDates = input.required<boolean>();
  readonly intervalInDays = model.required<number>();
  readonly selectedTab: WritableSignal<string> = signal<string>('stock_price');

  readonly kibanaUrl = computed<SafeResourceUrl>(() => {
    const symbol = encodeURIComponent(this.keyTicker());
    const baseUrl = 'https://kibana.quaks.ai/app/dashboards';

    let dashboardId = '';
    if (this.selectedTab() === 'stock_price') {
      dashboardId = DASHBOARD_IDS.stocks_eod_ohlcv;
    } else if(this.selectedTab() === 'indicator_ema'){
      dashboardId = DASHBOARD_IDS.stocks_eod_indicator_ema;
    }

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

}
