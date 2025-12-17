import { TestBed } from '@angular/core/testing';

import { MarketsNewsService } from './markets-news.service';

describe('NewsService', () => {
  let service: MarketsNewsService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MarketsNewsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
