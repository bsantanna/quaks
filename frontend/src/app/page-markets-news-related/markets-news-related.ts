import {Component, computed, effect, inject, OnDestroy, PLATFORM_ID, signal, WritableSignal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {toSignal} from '@angular/core/rxjs-interop';
import {ActivatedRoute, ParamMap, Params} from '@angular/router';
import {ShareUrlService, StockEodActions, StockInfoHeader, IndexedKeyTickerService, NewsFeed, SeoService} from '../shared';

@Component({
  selector: 'app-markets-news-related',
  imports: [
    StockEodActions,
    StockInfoHeader,
    NewsFeed
  ],
  templateUrl: './markets-news-related.html',
  styleUrl: './markets-news-related.scss',
})
export class MarketsNewsRelated implements OnDestroy {

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
  private readonly routeTitle = this.route.snapshot.title ?? '';

  constructor() {
    effect(() => {
      const ticker = this.keyTicker();
      const name = this.companyName();
      const linkTitle = `${this.routeTitle} - ${ticker}`;
      if (this.isBrowser) {
        this.shareUrlService.update({
          title: linkTitle,
          url: `${globalThis.location.href.split('?')[0]}`
        });
      }
      this.seoService.update({
        title: `${name || ticker} (${ticker}) News Feed`,
        description: `Latest market news and updates related to ${name || ticker} (${ticker}).`,
        path: `/markets/news/related/${ticker}`,
      });
    });
  }

  ngOnDestroy(): void {
    this.shareUrlService.update({title: '', url: ''});
    this.seoService.reset();
  }

}
