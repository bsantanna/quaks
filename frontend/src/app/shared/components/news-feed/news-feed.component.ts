import {Component, computed, effect, inject, input} from '@angular/core';
import {MarketsNewsService} from '../../services/markets-news.service';
import {take} from 'rxjs';
import {NewsMediaCards} from './news-media-cards/news-media-cards';

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
  readonly newsList = this.marketsNewsService.newsList;
  readonly newsItems = computed(() => this.newsList().items);

  constructor() {
    effect(() => {
      this.marketsNewsService.getNewsList(
        this.indexName(),
        this.keyTicker(),
        10,
        true,
        ''
      ).pipe(take(1)).subscribe(newsList => {
        this.marketsNewsService.newsList.set(newsList);
      });
    });
  }
}
