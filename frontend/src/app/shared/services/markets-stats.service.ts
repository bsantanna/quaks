import {inject, Injectable, signal, WritableSignal} from '@angular/core';
import {environment} from '../../../environments/environment';
import {HttpClient} from '@angular/common/http';
import {StatsClose} from '../models/markets.model';
import {catchError, Observable, of, timeout} from 'rxjs';
import {REQUEST_TIMEOUT} from '../../constants';

@Injectable({
  providedIn: 'root',
})
export class MarketsStatsService {

  private readonly httpClient = inject(HttpClient);

  private readonly marketsStatsCloseUrl = `${environment.apiBaseUrl}/markets/stats_close`;

  static readonly INITIAL_STATS_CLOSE: StatsClose = {
    key_ticker: '',
    most_recent_close: 0,
    most_recent_date: '',
    percent_variance: 0,
    most_recent_low:0,
    most_recent_high:0,
    most_recent_volume:0,
    most_recent_open:0
  };

  readonly statsClose: WritableSignal<StatsClose> = signal(MarketsStatsService.INITIAL_STATS_CLOSE);

  getStatsClose(
    indexName: string,
    ticker: string,
    intervalInDates: string,
  ): Observable<StatsClose> {

    const url = `${this.marketsStatsCloseUrl}/${encodeURIComponent(indexName)}/${encodeURIComponent(ticker)}`;
    const params = {
      start_date: intervalInDates.split('_')[0],
      end_date: intervalInDates.split('_')[1]
    };

    return this.httpClient.get<StatsClose>(url, {params}).pipe(
      timeout(REQUEST_TIMEOUT),
      catchError((error) => {
        console.error(`Failed to fetch latest close for ${ticker} @ ${indexName}`, error);
        return of(MarketsStatsService.INITIAL_STATS_CLOSE);
      })
    );

  }

}
