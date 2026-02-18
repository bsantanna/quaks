import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { MarketsNewsService } from './markets-news.service';

describe('NewsService', () => {
  let service: MarketsNewsService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()]
    });
    service = TestBed.inject(MarketsNewsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
