import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { IndexedKeyTickerService } from './indexed-key-ticker.service';

describe('IndexedKeyTickerService', () => {
  let service: IndexedKeyTickerService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()]
    });
    service = TestBed.inject(IndexedKeyTickerService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
