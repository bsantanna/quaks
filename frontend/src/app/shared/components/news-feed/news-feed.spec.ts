import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { NewsFeed } from './news-feed.component';

describe('NewsFeed', () => {
  let component: NewsFeed;
  let fixture: ComponentFixture<NewsFeed>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NewsFeed],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    }).compileComponents();

    fixture = TestBed.createComponent(NewsFeed);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('indexName', 'test-index');
    fixture.componentRef.setInput('keyTicker', 'AAPL');
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should create without keyTicker', async () => {
    const f = TestBed.createComponent(NewsFeed);
    f.componentRef.setInput('indexName', 'test-index');
    f.detectChanges();
    expect(f.componentInstance).toBeTruthy();
    expect(f.componentInstance.keyTicker()).toBe('');
    expect(f.componentInstance.searchTerm()).toBe('');
  });
});
