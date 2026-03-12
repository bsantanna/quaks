import {inject, Injectable} from '@angular/core';
import {environment} from '../../../environments/environment';
import {HttpClient} from '@angular/common/http';
import {InsightsNewsList} from '../models/markets.model';
import {catchError, Observable, of, timeout} from 'rxjs';
import {REQUEST_TIMEOUT} from '../../constants';

@Injectable({
  providedIn: 'root',
})
export class MarketsInsightsService {

  private readonly httpClient = inject(HttpClient);

  private readonly insightsNewsUrl = `${environment.apiBaseUrl}/markets/insights_news`;

  static readonly INITIAL_LIST: InsightsNewsList = {
    items: [],
    cursor: null
  }

  getInsightsNewsList(
    indexName: string,
    size: number,
    cursor: string,
    includeReportHtml: boolean = false,
  ): Observable<InsightsNewsList> {
    const url = `${this.insightsNewsUrl}/${encodeURIComponent(indexName)}`;
    const params: Record<string, string | number | boolean> = {
      size,
      include_report_html: includeReportHtml,
    };
    if (cursor) {
      params['cursor'] = cursor;
    }

    return this.httpClient.get<InsightsNewsList>(url, {params}).pipe(
      timeout(REQUEST_TIMEOUT),
      catchError((error) => {
        console.error(`Failed to fetch insights news @ ${indexName}`, error);
        return of(MarketsInsightsService.INITIAL_LIST);
      })
    );
  }

  getInsightsNewsItem(
    indexName: string,
    id: string,
  ): Observable<InsightsNewsList> {
    const url = `${this.insightsNewsUrl}/${encodeURIComponent(indexName)}`;
    const params = {
      id,
      size: 1,
      include_report_html: true,
    };

    return this.httpClient.get<InsightsNewsList>(url, {params}).pipe(
      timeout(REQUEST_TIMEOUT),
      catchError((error) => {
        console.error(`Failed to fetch insights news item ${id} @ ${indexName}`, error);
        return of(MarketsInsightsService.INITIAL_LIST);
      })
    );
  }
}
