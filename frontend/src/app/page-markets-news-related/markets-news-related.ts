import {Component, computed, effect, inject, OnDestroy, signal, WritableSignal} from '@angular/core';
import {toSignal} from '@angular/core/rxjs-interop';
import {ActivatedRoute, ParamMap, Params} from '@angular/router';
import {ShareUrlService} from '../shared/services/share-url.service';
import {StockEodActions} from '../shared/components/stock-eod-actions/stock-eod-actions';
import {StockInfoHeader} from '../shared/components/stock-info-header/stock-info-header';
import {IndexedKeyTickerService} from '../shared/services/indexed-key-ticker.service';
import {NewsFeed} from '../shared/components/news-feed/news-feed.component';
import {PathReactiveComponent} from '../shared/components/path-reactive.component';

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
export class MarketsNewsRelated extends PathReactiveComponent implements OnDestroy {

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

  constructor() {
    super();
    effect(() => {
      const ticker = this.keyTicker();
      const dates = this.intervalInDates();

      const linkTitle = `${this.title()} ${ticker}`;

      if (dates) {
        this.shareUrlService.update({
          title: linkTitle,
          url: window.location.href
        });
      } else {
        this.shareUrlService.update({
          title: linkTitle,
          url: `${window.location.href.split('?')[0]}`
        });
      }
    });
  }

  ngOnDestroy(): void {
    this.shareUrlService.update({title: '', url: ''});
  }

}
