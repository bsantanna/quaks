import {Component, computed, effect, inject, OnDestroy, PLATFORM_ID, signal, WritableSignal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {ActivatedRoute, Params, Router} from '@angular/router';
import {toSignal} from '@angular/core/rxjs-interop';
import {ShareUrlService, SeoService, DateFormatService} from '../shared';
import {StockComparisonAutocomplete} from './stock-comparison-autocomplete/stock-comparison-autocomplete';
import {StockComparisonCharts} from './stock-comparison-charts/stock-comparison-charts';
import {StockComparisonTime} from './stock-comparison-time/stock-comparison-time';
import {environment} from '../../environments/environment';

@Component({
  selector: 'app-markets-performance-comparison',
  imports: [StockComparisonAutocomplete, StockComparisonCharts, StockComparisonTime],
  templateUrl: './markets-performance-comparison.html',
  styleUrl: './markets-performance-comparison.scss',
})
export class MarketsPerformanceComparison implements OnDestroy {

  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly shareUrlService = inject(ShareUrlService);
  private readonly seoService = inject(SeoService);
  private readonly dateFormatService = inject(DateFormatService);

  private readonly queryParams = toSignal<Params>(this.route.queryParams);
  readonly symbols = computed(() => {
    const q = this.queryParams()?.['q'] ?? '';
    return q ? q.split(',').map((s: string) => s.trim()).filter((s: string) => s.length > 0) : [];
  });
  readonly intervalInDates = computed<string>(() => this.queryParams()?.['interval'] ?? '');
  readonly intervalInDays: WritableSignal<number> = signal<number>(365);
  readonly useIntervalInDates = computed<boolean>(() => this.intervalInDates().trim().length > 0);
  readonly isProduction = environment.production;
  readonly formattedInterval = computed(() => {
    const raw = this.intervalInDates();
    if (!raw.includes('_')) return {from: '', to: ''};
    const [from, to] = raw.split('_');
    const fmt = (d: string) => this.dateFormatService.format(d);
    return {from: fmt(from), to: fmt(to)};
  });
  private readonly routeTitle = this.route.snapshot.title ?? '';

  constructor() {
    effect(() => {
      const syms = this.symbols();
      const linkTitle = `${this.routeTitle} ${syms.join(',')}`;
      const useInterval = this.useIntervalInDates();
      if (this.isBrowser) {
        const url = useInterval
          ? window.location.href
          : `${window.location.href.split('?')[0]}?q=${syms.join(',')}&interval=${this.shareUrlService.getPastDateInDays(this.intervalInDays())}_${this.shareUrlService.getPastDateInDays(1)}`;
        this.shareUrlService.update({title: linkTitle, url});
      }
      this.seoService.update({
        title: syms.length ? `${syms.join(' vs ')} Performance Comparison` : 'Stock Performance Comparison',
        description: syms.length
          ? `Compare stock performance of ${syms.join(', ')} with interactive charts and technical analysis.`
          : 'Compare stock performance across multiple symbols with interactive charts.',
        path: '/markets/performance',
      });
    });
  }

  ngOnDestroy(): void {
    this.shareUrlService.update({title: '', url: ''});
    this.seoService.reset();
  }

  updateSymbols(symbols: string[]) {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {q: symbols.join(',')},
      queryParamsHandling: 'merge',
    });
  }

}
