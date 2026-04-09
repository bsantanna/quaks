import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import {ActivatedRoute, convertToParamMap} from '@angular/router';
import { of } from 'rxjs';

import { MarketsNewsItem } from './markets-news-item.component';
import {DateFormatService, MarketsNewsService, SeoService, ShareUrlService} from '../shared';
import {IndexedKeyTickerService} from '../shared/services/indexed-key-ticker.service';

describe('MarketsNewsArticle', () => {
  let component: MarketsNewsItem;
  let fixture: ComponentFixture<MarketsNewsItem>;
  const marketsNewsService = {
    newsList: signal({items: [], cursor: null}),
    getNewsItem: jest.fn(),
  };
  const indexedKeyTickerService = {
    indexedKeyTickers: jest.fn().mockReturnValue([{key_ticker: 'AAPL'}]),
  };
  const shareUrlService = {
    update: jest.fn(),
  };
  const seoService = {
    update: jest.fn(),
    setNewsArticleSchema: jest.fn(),
    reset: jest.fn(),
  };
  const dateFormatService = {
    format: jest.fn((value: string) => value),
    toAngularFormat: jest.fn(() => 'dd/MM/yy'),
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    marketsNewsService.newsList.set({items: [], cursor: null});
    marketsNewsService.getNewsItem.mockReturnValue(of({
      items: [{
        id: 'news-1',
        date: '2026-04-09T10:00:00Z',
        source: 'Benzinga',
        headline: 'News headline',
        summary: 'News summary',
        content: 'content',
        images: [{url: 'https://quaks.ai/news.png', size: 'large'}],
      }],
      cursor: null,
    }));

    await TestBed.configureTestingModule({
      imports: [MarketsNewsItem],
      providers: [
        {provide: ActivatedRoute, useValue: {paramMap: of(convertToParamMap({indexName: 'news-index', newsItemId: 'news-1'}))}},
        {provide: MarketsNewsService, useValue: marketsNewsService},
        {provide: IndexedKeyTickerService, useValue: indexedKeyTickerService},
        {provide: ShareUrlService, useValue: shareUrlService},
        {provide: SeoService, useValue: seoService},
        {provide: DateFormatService, useValue: dateFormatService},
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MarketsNewsItem);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('loads the news item and updates metadata', () => {
    expect(marketsNewsService.getNewsItem).toHaveBeenCalledWith('news-index', 'news-1');
    expect(marketsNewsService.newsList().items).toHaveLength(1);
    expect(shareUrlService.update).toHaveBeenCalledWith({
      title: 'News headline',
      url: 'http://localhost/',
    });
    expect(seoService.update).toHaveBeenCalledWith({
      title: 'News headline',
      description: 'News summary',
      path: '/markets/news/item/news-index/news-1',
      image: 'https://quaks.ai/news.png',
    });
    expect(seoService.setNewsArticleSchema).toHaveBeenCalled();
  });

  it('sanitizes html and rewrites ticker links', () => {
    const html = component.sanitizeHtml(
      '<script>alert(1)</script><a href="https://www.benzinga.com/quote/AAPL" onclick="hack()">AAPL</a>'
    );

    expect(html).toContain('href="/markets/stocks/AAPL"');
    expect(html).not.toContain('<script');
    expect(html).not.toContain('onclick=');
  });

  it('falls back to a generic title when no item exists', () => {
    marketsNewsService.getNewsItem.mockReturnValueOnce(of({items: [], cursor: null}));

    fixture = TestBed.createComponent(MarketsNewsItem);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(seoService.update).toHaveBeenLastCalledWith({
      title: 'Breaking news',
      description: undefined,
      path: '/markets/news/item/news-index/news-1',
      image: undefined,
    });
  });

  it('resets metadata on destroy', () => {
    component.ngOnDestroy();
    expect(shareUrlService.update).toHaveBeenLastCalledWith({title: '', url: ''});
    expect(seoService.reset).toHaveBeenCalled();
  });
});
