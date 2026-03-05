import {Component, computed, inject} from '@angular/core';
import {toSignal} from '@angular/core/rxjs-interop';
import {ActivatedRoute, Params} from '@angular/router';
import {NewsFeed} from '../shared/components/news-feed/news-feed.component';
import {SeoService} from '../shared';

@Component({
  selector: 'app-markets-news',
  imports: [NewsFeed],
  templateUrl: './markets-news.html',
  styleUrl: './markets-news.scss',
})
export class MarketsNews {
  private readonly route = inject(ActivatedRoute);
  private readonly queryParams = toSignal<Params>(this.route.queryParams);
  readonly searchTerm = computed(() => this.queryParams()?.['search_term'] ?? '');

  constructor() {
    inject(SeoService).update({
      title: 'Market News',
      description: 'Latest financial market news, earnings reports, and stock market updates.',
      path: '/markets/news',
    });
  }
}
