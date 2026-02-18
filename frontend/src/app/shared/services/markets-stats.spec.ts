import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { MarketsStatsService } from './markets-stats.service';

describe('MarketsStats', () => {
  let service: MarketsStatsService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()]
    });
    service = TestBed.inject(MarketsStatsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
