import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NewsList } from './news-list';
import { NewsItem } from '../../../models/markets.model';

describe('NewsList', () => {
  let component: NewsList;
  let fixture: ComponentFixture<NewsList>;

  const mockNewsItems: NewsItem[] = [
    {
      id: '1',
      date: '2026-01-15',
      source: 'reuters',
      headline: 'First headline',
      summary: 'First summary text',
      content: 'First content',
      images: [{ url: 'https://example.com/img1.jpg', size: 'thumb' }],
      key_ticker: ['AAPL'],
    },
    {
      id: '2',
      date: '2026-01-16',
      source: 'bloomberg',
      headline: 'Second headline',
      summary: 'Second summary text',
      content: 'Second content',
      images: [],
      key_ticker: [],
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NewsList],
    }).compileComponents();

    fixture = TestBed.createComponent(NewsList);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('newsItems', mockNewsItems);
    fixture.componentRef.setInput('indexName', 'markets-news');
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render a list item for each news item', () => {
    const links = fixture.nativeElement.querySelectorAll('a');
    expect(links.length).toBe(2);
  });

  it('should display headline and summary for each item', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('First headline');
    expect(el.textContent).toContain('Second headline');
    expect(el.textContent).toContain('First summary text');
    expect(el.textContent).toContain('Second summary text');
  });

  it('should display source for each item', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('reuters');
    expect(el.textContent).toContain('bloomberg');
  });

  it('should show key_ticker badge when present', () => {
    const badges = fixture.nativeElement.querySelectorAll('.news-ticker-badge');
    expect(badges.length).toBe(1);
    expect(badges[0].textContent.trim()).toBe('AAPL');
  });

  it('should build correct href for each item', () => {
    const links = fixture.nativeElement.querySelectorAll('a');
    expect(links[0].getAttribute('href')).toContain('markets-news');
    expect(links[0].getAttribute('href')).toContain('1');
  });

  it('should render with empty items array', () => {
    fixture.componentRef.setInput('newsItems', []);
    fixture.detectChanges();

    const links = fixture.nativeElement.querySelectorAll('a');
    expect(links.length).toBe(0);
  });
});
