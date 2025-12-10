import { TestBed } from '@angular/core/testing';

import { IndexedKeyTickerService } from './indexed-key-ticker.service';

describe('IndexedKeyTickerService', () => {
  let service: IndexedKeyTickerService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(IndexedKeyTickerService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
