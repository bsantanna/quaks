import {Component, computed, effect, inject, input, signal} from '@angular/core';
import {MarketsNewsService} from '../../services/markets-news.service';
import {take} from 'rxjs';
import {NewsMediaCards} from './news-media-cards/news-media-cards';
import {NewsItem} from '../../models/markets.model';

@Component({
  selector: 'app-news-feed',
  imports: [
    NewsMediaCards
  ],
  templateUrl: './news-feed.html',
  styleUrl: './news-feed.scss',
})
export class NewsFeed {
  private readonly marketsNewsService = inject(MarketsNewsService);

  readonly indexName = input.required<string>();
  readonly keyTicker = input.required<string>();

  readonly newsItems = signal<NewsItem[]>([]);
  readonly cursor = signal<string | null>(null);
  readonly loading = signal(false);
  readonly hasMore = computed(() => this.cursor() !== null);

  constructor() {
    effect(() => {
      const indexName = this.indexName();
      const keyTicker = this.keyTicker();
      this.newsItems.set([]);
      this.cursor.set(null);
      this.fetchNews(indexName, keyTicker, '');
    });
  }

  loadMore(): void {
    const currentCursor = this.cursor();
    if (currentCursor === null || this.loading()) return;
    this.fetchNews(this.indexName(), this.keyTicker(), currentCursor);
  }

  private fetchNews(indexName: string, keyTicker: string, cursor: string): void {
    this.loading.set(true);
    this.marketsNewsService.getNewsList(
      indexName,
      keyTicker,
      10,
      true,
      cursor
    ).pipe(take(1)).subscribe(newsList => {
      this.newsItems.update(current => [...current, ...newsList.items]);
      this.cursor.set(newsList.cursor);
      this.marketsNewsService.newsList.set(newsList);
      this.loading.set(false);
    });
  }
}
