import {Component, computed, effect, inject, OnDestroy, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {HttpClient} from '@angular/common/http';
import {ActivatedRoute, ParamMap, RouterLink} from '@angular/router';
import {toSignal} from '@angular/core/rxjs-interop';
import {take} from 'rxjs';
import {CompanyProfile} from '../shared/models/markets.model';
import {MarketsStatsService} from '../shared/services/markets-stats.service';
import {IndexedKeyTickerService} from '../shared/services/indexed-key-ticker.service';
import {SeoService} from '../shared/services/seo.service';
import {STOCK_EXCHANGE_FLAGS} from '../constants';

@Component({
  selector: 'app-markets-profile',
  imports: [RouterLink],
  templateUrl: './markets-profile.html',
  styleUrl: './markets-profile.scss',
})
export class MarketsProfile implements OnDestroy {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly httpClient = inject(HttpClient);
  private readonly marketsStatsService = inject(MarketsStatsService);
  private readonly indexedKeyTickerService = inject(IndexedKeyTickerService);
  private readonly seoService = inject(SeoService);

  private readonly paramMap = toSignal<ParamMap>(this.route.paramMap);
  readonly keyTicker = computed(() => this.paramMap()?.get('keyTicker') ?? '');
  readonly indexName = computed(() => {
    const entry = this.indexedKeyTickerService.findKeyTicker(this.keyTicker());
    return entry ? `quaks_stocks-metadata_${entry.index}` : 'quaks_stocks-metadata_latest';
  });
  readonly exchangeFlag = computed(() => {
    const entry = this.indexedKeyTickerService.findKeyTicker(this.keyTicker());
    return entry ? (STOCK_EXCHANGE_FLAGS[entry.index] ?? '') : '';
  });

  private readonly companyDescriptions = toSignal(
    this.httpClient.get<Record<string, string>>('/json/company_descriptions.json'),
    {initialValue: {} as Record<string, string>}
  );

  readonly companyAbout = computed(() => {
    const ticker = this.keyTicker();
    const curated = this.companyDescriptions()[ticker];
    if (curated) return curated;
    return this.profile()?.description ?? null;
  });

  readonly profile = signal<CompanyProfile | null>(null);
  readonly loading = signal(true);

  constructor() {
    effect(() => {
      const ticker = this.keyTicker();
      const index = this.indexName();
      if (!ticker) return;

      this.loading.set(true);
      this.marketsStatsService.getCompanyProfile(index, ticker)
        .pipe(take(1))
        .subscribe(p => {
          this.profile.set(p);
          this.loading.set(false);

          this.seoService.update({
            title: p.name ? `${ticker} - ${p.name} Company Profile` : `${ticker} Company Profile`,
            description: p.description
              ? p.description.substring(0, 160)
              : `Company profile and financial data for ${ticker}.`,
            path: `/markets/profile/${ticker}`,
          });
        });
    });
  }

  ngOnDestroy(): void {
    this.seoService.reset();
  }

  formatLargeNumber(value: number | null | undefined): string {
    if (value == null) return '--';
    const abs = Math.abs(value);
    if (abs >= 1_000_000_000_000) return (value / 1_000_000_000_000).toFixed(2) + 'T';
    if (abs >= 1_000_000_000) return (value / 1_000_000_000).toFixed(2) + 'B';
    if (abs >= 1_000_000) return (value / 1_000_000).toFixed(2) + 'M';
    if (abs >= 1_000) return (value / 1_000).toFixed(1) + 'K';
    return value.toFixed(2);
  }

  formatPercent(value: number | null | undefined): string {
    if (value == null) return '--';
    return (value * 100).toFixed(2) + '%';
  }

  formatNumber(value: number | null | undefined, decimals: number = 2): string {
    if (value == null) return '--';
    return value.toFixed(decimals);
  }

  formatDate(value: string | null | undefined): string {
    if (!value) return '--';
    const [y, m, d] = value.split('-');
    return `${d}/${m}/${y}`;
  }

}
