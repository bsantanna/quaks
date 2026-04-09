import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';

import { MarketsStatsService } from './markets-stats.service';

describe('MarketsStats', () => {
  let service: MarketsStatsService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()]
    });
    service = TestBed.inject(MarketsStatsService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('fetches a company profile and falls back on error', () => {
    let successResult: unknown;
    service.getCompanyProfile('stocks', 'AAPL').subscribe(result => {
      successResult = result;
    });

    const successReq = httpMock.expectOne(req =>
      req.method === 'GET' && req.url.endsWith('/markets/profile/stocks/AAPL')
    );
    successReq.flush({key_ticker: 'AAPL', name: 'Apple'});
    expect(successResult).toEqual({key_ticker: 'AAPL', name: 'Apple'});

    let fallbackResult: unknown;
    service.getCompanyProfile('stocks', 'MSFT').subscribe(result => {
      fallbackResult = result;
    });

    const errorReq = httpMock.expectOne(req =>
      req.method === 'GET' && req.url.endsWith('/markets/profile/stocks/MSFT')
    );
    errorReq.flush('boom', {status: 500, statusText: 'Server Error'});
    expect(fallbackResult).toEqual({key_ticker: 'MSFT'});
  });

  it('fetches stats close data and falls back on error', () => {
    let successResult: unknown;
    service.getStatsClose('stocks', 'AAPL', '2026-04-01_2026-04-09').subscribe(result => {
      successResult = result;
    });

    const successReq = httpMock.expectOne(req =>
      req.method === 'GET'
      && req.url.endsWith('/markets/stats_close/stocks/AAPL')
      && req.params.get('start_date') === '2026-04-01'
      && req.params.get('end_date') === '2026-04-09'
    );
    successReq.flush({key_ticker: 'AAPL', percent_variance: 1});
    expect(successResult).toEqual({key_ticker: 'AAPL', percent_variance: 1});

    let fallbackResult: unknown;
    service.getStatsClose('stocks', 'AAPL', '2026-04-01_2026-04-09').subscribe(result => {
      fallbackResult = result;
    });

    const errorReq = httpMock.expectOne(req => req.url.endsWith('/markets/stats_close/stocks/AAPL'));
    errorReq.flush('boom', {status: 500, statusText: 'Server Error'});
    expect(fallbackResult).toEqual(MarketsStatsService.INITIAL_STATS_CLOSE);
  });

  it('fetches bulk close stats with optional dates and falls back on error', () => {
    let successResult: unknown;
    service.getStatsCloseBulk('bulk-index', ['AAPL', 'MSFT'], '2026-04-01', '2026-04-09').subscribe(result => {
      successResult = result;
    });

    const successReq = httpMock.expectOne(req =>
      req.method === 'GET'
      && req.url.endsWith('/markets/stats_close_bulk/bulk-index')
      && req.params.get('key_tickers') === 'AAPL,MSFT'
      && req.params.get('start_date') === '2026-04-01'
      && req.params.get('end_date') === '2026-04-09'
    );
    successReq.flush({items: [{key_ticker: 'AAPL'}]});
    expect(successResult).toEqual({items: [{key_ticker: 'AAPL'}]});

    let fallbackResult: unknown;
    service.getStatsCloseBulk('bulk-index', ['AAPL']).subscribe(result => {
      fallbackResult = result;
    });

    const errorReq = httpMock.expectOne(req =>
      req.method === 'GET'
      && req.url.endsWith('/markets/stats_close_bulk/bulk-index')
      && req.params.get('key_tickers') === 'AAPL'
    );
    errorReq.flush('boom', {status: 500, statusText: 'Server Error'});
    expect(fallbackResult).toEqual({items: []});
  });

  it('fetches bulk market caps and falls back on error', () => {
    let successResult: unknown;
    service.getMarketCapsBulk('bulk-index', ['AAPL', 'MSFT']).subscribe(result => {
      successResult = result;
    });

    const successReq = httpMock.expectOne(req =>
      req.method === 'GET'
      && req.url.endsWith('/markets/market_caps_bulk/bulk-index')
      && req.params.get('key_tickers') === 'AAPL,MSFT'
    );
    successReq.flush({items: [{key_ticker: 'AAPL', market_capitalization: 100}]});
    expect(successResult).toEqual({items: [{key_ticker: 'AAPL', market_capitalization: 100}]});

    let fallbackResult: unknown;
    service.getMarketCapsBulk('bulk-index', ['AAPL']).subscribe(result => {
      fallbackResult = result;
    });

    const errorReq = httpMock.expectOne(req =>
      req.method === 'GET'
      && req.url.endsWith('/markets/market_caps_bulk/bulk-index')
      && req.params.get('key_tickers') === 'AAPL'
    );
    errorReq.flush('boom', {status: 500, statusText: 'Server Error'});
    expect(fallbackResult).toEqual({items: []});
  });
});
