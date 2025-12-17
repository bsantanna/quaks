import {inject, Injectable, signal, WritableSignal} from '@angular/core';
import {environment} from '../../../environments/environment';
import {HttpClient} from '@angular/common/http';
import {NewsList} from '../models/markets.model';
import {catchError, Observable, of, timeout} from 'rxjs';
import {REQUEST_TIMEOUT} from '../../constants';

@Injectable({
  providedIn: 'root',
})
export class MarketsNewsService {

  private readonly httpClient = inject(HttpClient);

  private readonly marketsNewsUrl = `${environment.apiBaseUrl}/markets/news`;

  static readonly INITIAL_NEWS_LIST: NewsList = {
    items: [],
    cursor: ''
  }

  readonly newsList: WritableSignal<NewsList> = signal(MarketsNewsService.INITIAL_NEWS_LIST);

  getNewsItem(
    indexName: string,
    id: string
  ): Observable<NewsList> {
    const url = `${this.marketsNewsUrl}/${encodeURIComponent(indexName)}`;
    const params = {
      id,
      size: 1,
      include_text_content: true,
      include_obj_images: true
    };

    return this.httpClient.get<NewsList>(url, {params}).pipe(
      timeout(REQUEST_TIMEOUT),
      catchError((error) => {
        console.error(`Failed to fetch news for ${id} @ ${indexName}`, error);
        return of(MarketsNewsService.INITIAL_NEWS_LIST);
      })
    );

  }

  getNewsList(
    indexName: string,
    ticker: string,
    size: number,
    includeImages: boolean,
    cursor: string,
  ): Observable<NewsList> {
    const url = `${this.marketsNewsUrl}/${encodeURIComponent(indexName)}`;
    const params = {
      key_ticker: ticker,
      size,
      cursor,
      include_obj_images: includeImages,
    };

    return this.httpClient.get<NewsList>(url, {params}).pipe(
      timeout(REQUEST_TIMEOUT),
      catchError((error) => {
        console.error(`Failed to fetch news for ${ticker} @ ${indexName}`, error);
        return of(MarketsNewsService.INITIAL_NEWS_LIST);
      })
    )

  }

}
