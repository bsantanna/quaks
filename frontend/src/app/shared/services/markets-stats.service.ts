import {inject, Injectable, signal, WritableSignal} from '@angular/core';
import {environment} from '../../../environments/environment';
import {HttpClient} from '@angular/common/http';
import {CompanyProfile, MarketCapsBulkResponse, StatsClose, StatsCloseBulkResponse} from '../models/markets.model';
import {catchError, Observable, of, timeout} from 'rxjs';
import {REQUEST_TIMEOUT} from '../../constants';

@Injectable({
  providedIn: 'root',
})
export class MarketsStatsService {

  private readonly httpClient = inject(HttpClient);

  private readonly marketsProfileUrl = `${environment.apiBaseUrl}/markets/profile`;
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

  getCompanyProfile(
    indexName: string,
    ticker: string,
  ): Observable<CompanyProfile> {
    const url = `${this.marketsProfileUrl}/${encodeURIComponent(indexName)}/${encodeURIComponent(ticker)}`;
    return this.httpClient.get<CompanyProfile>(url).pipe(
      timeout(REQUEST_TIMEOUT),
      catchError((error) => {
        console.error(`Failed to fetch company profile for ${ticker} @ ${indexName}`, error);
        return of({key_ticker: ticker} as CompanyProfile);
      })
    );
  }

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

  getStatsCloseBulk(
    indexName: string,
    keyTickers: string[],
  ): Observable<StatsCloseBulkResponse> {
    const url = `${environment.apiBaseUrl}/markets/stats_close_bulk/${encodeURIComponent(indexName)}`;
    const params = {key_tickers: keyTickers.join(',')};
    return this.httpClient.get<StatsCloseBulkResponse>(url, {params}).pipe(
      timeout(REQUEST_TIMEOUT),
      catchError((error) => {
        console.error(`Failed to fetch bulk stats close for ${indexName}`, error);
        return of({items: []});
      })
    );
  }

  getMarketCapsBulk(
    indexName: string,
    keyTickers: string[],
  ): Observable<MarketCapsBulkResponse> {
    const url = `${environment.apiBaseUrl}/markets/market_caps_bulk/${encodeURIComponent(indexName)}`;
    const params = {key_tickers: keyTickers.join(',')};
    return this.httpClient.get<MarketCapsBulkResponse>(url, {params}).pipe(
      timeout(REQUEST_TIMEOUT),
      catchError((error) => {
        console.error(`Failed to fetch bulk market caps for ${indexName}`, error);
        return of({items: []});
      })
    );
  }

}
