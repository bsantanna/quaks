import {Component, computed, inject, input} from '@angular/core';
import {DomSanitizer, SafeResourceUrl} from '@angular/platform-browser';
import {DASHBOARDS_IDS, IFRAME_STYLE, DASHBOARDS_ENDPOINT} from '../../constants';

@Component({
  selector: 'app-stock-comparison-charts',
  imports: [],
  templateUrl: './stock-comparison-charts.html',
  styleUrl: './stock-comparison-charts.scss',
})
export class StockComparisonCharts {

  private readonly sanitizer = inject(DomSanitizer);

  readonly symbols = input.required<string[]>();
  readonly intervalInDays = input<number>(365);

  readonly kibanaUrl = computed<SafeResourceUrl>(() => {
    const symbols = this.symbols();
    if (symbols.length === 0) {
      return this.sanitizer.bypassSecurityTrustResourceUrl('about:blank');
    }

    const query = symbols
      .map(s => `key_ticker:${encodeURIComponent(s)}`)
      .join(' OR ');

    const dashboardId = DASHBOARDS_IDS.stocks_comparison;
    const days = this.intervalInDays();

    const embedParams = new URLSearchParams({
      embed: 'true',
      'show-time-filter': 'false',
      'hide-filter-bar': 'true',
      '_g': `(refreshInterval:(pause:!t,value:60000),time:(from:now-${days}d,to:now))`,
      '_a': `(query:(language:kuery,query:'${query}'))`
    });

    const fullUrl = `${DASHBOARDS_ENDPOINT}?auth_provider_hint=anonymous1#/view/${dashboardId}?${embedParams.toString()}`;
    return this.sanitizer.bypassSecurityTrustResourceUrl(fullUrl); // NOSONAR — safe: URL built from app constants + encodeURIComponent'd ticker symbols
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
