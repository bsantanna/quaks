import {Component, computed, effect, inject, OnDestroy, signal, WritableSignal} from '@angular/core';
import {toSignal} from '@angular/core/rxjs-interop';
import {ActivatedRoute, ParamMap, Params} from '@angular/router';
import {ShareUrlService, StockEodActions, StockInfoHeader, IndexedKeyTickerService, NewsFeed} from '../shared';

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

  private readonly route = inject(ActivatedRoute);
  private readonly shareUrlService = inject(ShareUrlService);
  private readonly indexedKeyTickerService = inject(IndexedKeyTickerService);

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
      const linkTitle = `${this.routeTitle} - ${this.keyTicker()}`;
      this.shareUrlService.update({
        title: linkTitle,
        url: `${window.location.href.split('?')[0]}`
      });
    });
  }

  ngOnDestroy(): void {
    this.shareUrlService.update({title: '', url: ''});
  }

}
