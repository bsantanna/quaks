import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { MarketsNewsService } from './markets-news.service';
import { NewsList } from '../models/markets.model';
import { environment } from '../../../environments/environment';

describe('MarketsNewsService', () => {
  let service: MarketsNewsService;
  let httpTesting: HttpTestingController;

  const baseUrl = `${environment.apiBaseUrl}/markets/news`;

  const mockNewsList: NewsList = {
    items: [
      {
        headline: 'Test headline',
        summary: 'Test summary',
        source: 'test-source',
        url: 'https://example.com/news/1',
        key_ticker: ['AAPL'],
      } as any,
    ],
    cursor: 'next-cursor-token',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MarketsNewsService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should initialize newsList signal with INITIAL_NEWS_LIST', () => {
    expect(service.newsList()).toEqual(MarketsNewsService.INITIAL_NEWS_LIST);
  });

  it('INITIAL_NEWS_LIST should have empty items and null cursor', () => {
    expect(MarketsNewsService.INITIAL_NEWS_LIST.items).toEqual([]);
    expect(MarketsNewsService.INITIAL_NEWS_LIST.cursor).toBeNull();
  });

  describe('getNewsItem', () => {
    it('should make GET request with correct URL and params', () => {
      service.getNewsItem('markets-news', 'doc-123').subscribe((result) => {
        expect(result).toEqual(mockNewsList);
      });

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/markets-news`
      );
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('id')).toBe('doc-123');
      expect(req.request.params.get('size')).toBe('1');
      expect(req.request.params.get('include_text_content')).toBe('true');
      expect(req.request.params.get('include_obj_images')).toBe('true');
      req.flush(mockNewsList);
    });

    it('should encode indexName in the URL', () => {
      service.getNewsItem('markets/news index', 'doc-1').subscribe();

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/markets%2Fnews%20index`
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockNewsList);
    });

    it('should return INITIAL_NEWS_LIST on HTTP error', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      service.getNewsItem('markets-news', 'bad-id').subscribe((result) => {
        expect(result).toEqual(MarketsNewsService.INITIAL_NEWS_LIST);
      });

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/markets-news`
      );
      req.flush('Server error', { status: 500, statusText: 'Internal Server Error' });

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to fetch news for bad-id @ markets-news'),
        expect.anything()
      );
      consoleSpy.mockRestore();
    });
  });

  describe('getNewsList', () => {
    it('should make GET request with correct params (no cursor)', () => {
      service.getNewsList('markets-news', 'AAPL', 10, true, '').subscribe((result) => {
        expect(result).toEqual(mockNewsList);
      });

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/markets-news`
      );
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('key_ticker')).toBe('AAPL');
      expect(req.request.params.get('size')).toBe('10');
      expect(req.request.params.get('include_obj_images')).toBe('true');
      expect(req.request.params.has('cursor')).toBe(false);
      req.flush(mockNewsList);
    });

    it('should include cursor param when provided', () => {
      service.getNewsList('markets-news', 'TSLA', 5, false, 'abc123').subscribe((result) => {
        expect(result).toEqual(mockNewsList);
      });

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/markets-news`
      );
      expect(req.request.params.get('cursor')).toBe('abc123');
      expect(req.request.params.get('include_obj_images')).toBe('false');
      req.flush(mockNewsList);
    });

    it('should encode indexName in the URL', () => {
      service.getNewsList('special/index', 'MSFT', 5, false, '').subscribe();

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/special%2Findex`
      );
      req.flush(mockNewsList);
    });

    it('should return INITIAL_NEWS_LIST on HTTP error', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      service.getNewsList('markets-news', 'GOOG', 10, true, '').subscribe((result) => {
        expect(result).toEqual(MarketsNewsService.INITIAL_NEWS_LIST);
      });

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/markets-news`
      );
      req.flush('Not found', { status: 404, statusText: 'Not Found' });

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to fetch news for GOOG @ markets-news'),
        expect.anything()
      );
      consoleSpy.mockRestore();
    });

    it('should not include key_ticker when ticker is empty', () => {
      service.getNewsList('markets-news', '', 10, true, '').subscribe();

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/markets-news`
      );
      expect(req.request.params.has('key_ticker')).toBe(false);
      expect(req.request.params.has('search_term')).toBe(false);
      req.flush(mockNewsList);
    });

    it('should send search_term when ticker is empty and searchTerm is provided', () => {
      service.getNewsList('markets-news', '', 10, true, '', 'Bezos').subscribe();

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/markets-news`
      );
      expect(req.request.params.has('key_ticker')).toBe(false);
      expect(req.request.params.get('search_term')).toBe('Bezos');
      req.flush(mockNewsList);
    });

    it('should send key_ticker and ignore search_term when both are provided', () => {
      service.getNewsList('markets-news', 'AAPL', 10, true, '', 'Bezos').subscribe();

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/markets-news`
      );
      expect(req.request.params.get('key_ticker')).toBe('AAPL');
      expect(req.request.params.has('search_term')).toBe(false);
      req.flush(mockNewsList);
    });
  });
});
