import {Component, computed, effect, inject, input} from '@angular/core';
import {NewsItem} from '../../shared/models/markets.model';
import {DatePipe} from '@angular/common';
import {MarketsNewsService} from '../../shared/services/markets-news.service';
import {take} from 'rxjs';

@Component({
  selector: 'app-related-news-feed',
  imports: [
    DatePipe
  ],
  templateUrl: './related-news-feed.html',
  styleUrl: './related-news-feed.scss',
})
export class RelatedNewsFeed {

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
