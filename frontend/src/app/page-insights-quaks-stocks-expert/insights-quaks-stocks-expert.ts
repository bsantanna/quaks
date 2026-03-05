import {Component, computed, inject} from '@angular/core';
import {ActivatedRoute, ParamMap} from '@angular/router';
import {toSignal} from '@angular/core/rxjs-interop';
import {SeoService} from '../shared';

@Component({
  selector: 'app-insights-quaks-stocks-expert',
  imports: [],
  templateUrl: './insights-quaks-stocks-expert.html',
  styleUrl: './insights-quaks-stocks-expert.scss',
})
export class InsightsQuaksStocksExpert {
  private readonly route = inject(ActivatedRoute);
  private readonly seoService = inject(SeoService);
  private readonly paramMap = toSignal<ParamMap>(this.route.paramMap);
  readonly keyTicker = computed(() => this.paramMap()?.get('keyTicker') ?? '');

  constructor() {
    const ticker = this.route.snapshot.paramMap.get('keyTicker') ?? '';
    this.seoService.update({
      title: `${ticker} AI Stocks Expert Report`,
      description: `AI-generated expert analysis and insights for ${ticker} stock.`,
      path: `/insights/qse/${ticker}`,
    });
  }
}
