import {TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';

import {MarketsInsightsService} from './markets-insights.service';
import {InsightsNewsList} from '../models/markets.model';
import {environment} from '../../../environments/environment';

describe('MarketsInsightsService', () => {
  let service: MarketsInsightsService;
  let httpTesting: HttpTestingController;

  const baseUrl = `${environment.apiBaseUrl}/markets/insights_news`;

  const mockList: InsightsNewsList = {
    items: [
      {
        id: 'doc-1',
        headline: 'Test insight',
        summary: 'Summary text',
      } as any,
    ],
    cursor: 'next-cursor',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MarketsInsightsService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('INITIAL_LIST should have empty items and null cursor', () => {
    expect(MarketsInsightsService.INITIAL_LIST.items).toEqual([]);
    expect(MarketsInsightsService.INITIAL_LIST.cursor).toBeNull();
  });

  describe('getInsightsNewsList', () => {
    it('should make GET request with correct params (no cursor)', () => {
      service.getInsightsNewsList('insights-index', 10, '', false).subscribe((result) => {
        expect(result).toEqual(mockList);
      });

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/insights-index`
      );
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('size')).toBe('10');
      expect(req.request.params.get('include_report_html')).toBe('false');
      expect(req.request.params.has('cursor')).toBe(false);
      req.flush(mockList);
    });

    it('should include cursor param when provided', () => {
      service.getInsightsNewsList('insights-index', 5, 'abc123', true).subscribe();

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/insights-index`
      );
      expect(req.request.params.get('cursor')).toBe('abc123');
      expect(req.request.params.get('include_report_html')).toBe('true');
      req.flush(mockList);
    });

    it('should encode indexName in the URL', () => {
      service.getInsightsNewsList('special/index', 5, '', false).subscribe();

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/special%2Findex`
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockList);
    });

    it('should return INITIAL_LIST on HTTP error', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      service.getInsightsNewsList('insights-index', 10, '', false).subscribe((result) => {
        expect(result).toEqual(MarketsInsightsService.INITIAL_LIST);
      });

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/insights-index`
      );
      req.flush('Server error', {status: 500, statusText: 'Internal Server Error'});

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to fetch insights news @ insights-index'),
        expect.anything()
      );
      consoleSpy.mockRestore();
    });
  });

  describe('getInsightsNewsItem', () => {
    it('should make GET request with id, size=1, and include_report_html=true', () => {
      service.getInsightsNewsItem('insights-index', 'doc-123').subscribe((result) => {
        expect(result).toEqual(mockList);
      });

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/insights-index`
      );
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('id')).toBe('doc-123');
      expect(req.request.params.get('size')).toBe('1');
      expect(req.request.params.get('include_report_html')).toBe('true');
      req.flush(mockList);
    });

    it('should encode indexName in the URL', () => {
      service.getInsightsNewsItem('index/with/slashes', 'doc-1').subscribe();

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/index%2Fwith%2Fslashes`
      );
      req.flush(mockList);
    });

    it('should return INITIAL_LIST on HTTP error', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      service.getInsightsNewsItem('insights-index', 'bad-id').subscribe((result) => {
        expect(result).toEqual(MarketsInsightsService.INITIAL_LIST);
      });

      const req = httpTesting.expectOne(
        (r) => r.url === `${baseUrl}/insights-index`
      );
      req.flush('Not found', {status: 404, statusText: 'Not Found'});

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to fetch insights news item bad-id @ insights-index'),
        expect.anything()
      );
      consoleSpy.mockRestore();
    });
  });

  describe('getInsightsPreview', () => {
    it('should make GET request for preview', () => {
      const mockPreview = {doc_id: 'doc-1', status: 'ready', executive_summary: 'Summary', report_html: '<p>Report</p>'};

      service.getInsightsPreview('doc-1').subscribe(result => {
        expect(result).toEqual(mockPreview);
      });

      const req = httpTesting.expectOne(
        (r) => r.url === `${environment.apiBaseUrl}/markets/insights/preview/doc-1`
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockPreview);
    });

    it('should return null on HTTP error', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      service.getInsightsPreview('bad-id').subscribe(result => {
        expect(result).toBeNull();
      });

      const req = httpTesting.expectOne(
        (r) => r.url === `${environment.apiBaseUrl}/markets/insights/preview/bad-id`
      );
      req.flush('Not found', {status: 404, statusText: 'Not Found'});

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to fetch preview bad-id'),
        expect.anything()
      );
      consoleSpy.mockRestore();
    });
  });

  describe('cancelInsightsPreview', () => {
    it('should make POST request to cancel', () => {
      service.cancelInsightsPreview('doc-1').subscribe();

      const req = httpTesting.expectOne(
        (r) => r.url === `${environment.apiBaseUrl}/markets/insights/preview/doc-1/cancel`
      );
      expect(req.request.method).toBe('POST');
      req.flush(null);
    });
  });
});
