import {ComponentFixture, TestBed} from '@angular/core/testing';
import {Component, input} from '@angular/core';
import {of} from 'rxjs';

import {NewsFeed} from './news-feed.component';
import {MarketsNewsService} from '../../services/markets-news.service';
import {NewsItem, NewsList} from '../../models/markets.model';

@Component({
  selector: 'app-news-media-cards',
  template: '',
  standalone: true,
})
class MockNewsMediaCards {
  readonly newsItems = input.required<NewsItem[]>();
  readonly indexName = input.required<string>();
}

describe('NewsFeed', () => {
  let component: NewsFeed;
  let fixture: ComponentFixture<NewsFeed>;
  let marketsNewsService: jest.Mocked<Pick<MarketsNewsService, 'getNewsList' | 'newsList'>>;

  const mockNewsItem: NewsItem = {
    id: '1',
    date: '2026-01-01',
    source: 'test',
    headline: 'Test headline',
    summary: 'Test summary',
    content: 'Test content',
    images: [],
    key_ticker: ['AAPL'],
  };

  const mockNewsListPage1: NewsList = {
    items: [mockNewsItem],
    cursor: 'cursor-page-2',
  };

  const mockNewsListPage2: NewsList = {
    items: [{...mockNewsItem, id: '2', headline: 'Second page'}],
    cursor: null,
  };

  beforeEach(() => {
    marketsNewsService = {
      getNewsList: jest.fn().mockReturnValue(of(mockNewsListPage1)),
      newsList: {set: jest.fn()} as any,
    };

    TestBed.configureTestingModule({
      imports: [NewsFeed],
      providers: [
        {provide: MarketsNewsService, useValue: marketsNewsService},
      ],
    }).overrideComponent(NewsFeed, {
      set: {imports: [MockNewsMediaCards]},
    });

    fixture = TestBed.createComponent(NewsFeed);
    component = fixture.componentInstance;

    // Set required inputs
    fixture.componentRef.setInput('indexName', 'markets-news');
    fixture.componentRef.setInput('keyTicker', 'AAPL');
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should initialize with empty newsItems, null cursor, and loading false', () => {
    expect(component.newsItems()).toEqual([]);
    expect(component.cursor()).toBeNull();
    expect(component.loading()).toBe(false);
    expect(component.hasMore()).toBe(false);
  });

  it('should fetch news on init via the constructor effect', () => {
    fixture.detectChanges();

    expect(marketsNewsService.getNewsList).toHaveBeenCalledWith(
      'markets-news', 'AAPL', 10, true, ''
    );
    expect(component.newsItems()).toEqual([mockNewsItem]);
    expect(component.cursor()).toBe('cursor-page-2');
    expect(component.loading()).toBe(false);
    expect(component.hasMore()).toBe(true);
    expect(marketsNewsService.newsList.set).toHaveBeenCalledWith(mockNewsListPage1);
  });

  it('should reset and re-fetch when inputs change', () => {
    fixture.detectChanges();
    expect(marketsNewsService.getNewsList).toHaveBeenCalledTimes(1);

    marketsNewsService.getNewsList.mockReturnValue(of(mockNewsListPage2));
    fixture.componentRef.setInput('keyTicker', 'TSLA');
    fixture.detectChanges();

    expect(marketsNewsService.getNewsList).toHaveBeenCalledWith(
      'markets-news', 'TSLA', 10, true, ''
    );
    // Items should be reset (not appended to old ones)
    expect(component.newsItems()).toEqual(mockNewsListPage2.items);
    expect(component.cursor()).toBeNull();
    expect(component.hasMore()).toBe(false);
  });

  describe('loadMore', () => {
    it('should fetch next page using cursor and append items', () => {
      fixture.detectChanges();
      expect(component.newsItems().length).toBe(1);

      marketsNewsService.getNewsList.mockReturnValue(of(mockNewsListPage2));
      component.loadMore();

      expect(marketsNewsService.getNewsList).toHaveBeenCalledWith(
        'markets-news', 'AAPL', 10, true, 'cursor-page-2'
      );
      expect(component.newsItems().length).toBe(2);
      expect(component.newsItems()[1].id).toBe('2');
      expect(component.cursor()).toBeNull();
      expect(component.hasMore()).toBe(false);
      expect(component.loading()).toBe(false);
    });

    it('should not fetch when cursor is null', () => {
      fixture.detectChanges();
      component.cursor.set(null);
      marketsNewsService.getNewsList.mockClear();

      component.loadMore();

      expect(marketsNewsService.getNewsList).not.toHaveBeenCalled();
    });

    it('should not fetch when already loading', () => {
      fixture.detectChanges();
      component.loading.set(true);
      marketsNewsService.getNewsList.mockClear();

      component.loadMore();

      expect(marketsNewsService.getNewsList).not.toHaveBeenCalled();
    });
  });
});
