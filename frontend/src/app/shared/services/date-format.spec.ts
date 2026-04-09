import {PLATFORM_ID} from '@angular/core';
import {TestBed} from '@angular/core/testing';
import {DateFormatService} from './date-format.service';

describe('DateFormatService', () => {
  afterEach(() => {
    localStorage.clear();
    TestBed.resetTestingModule();
  });

  it('defaults to DD/MM/YY and formats values', () => {
    TestBed.configureTestingModule({});
    const service = TestBed.inject(DateFormatService);

    expect(service.state().dateFormat).toBe('DD/MM/YY');
    expect(service.format('2026-04-09')).toBe('09/04/26');
    expect(service.format('invalid')).toBe('invalid');
    expect(service.format(null)).toBe('--');
    expect(service.toAngularFormat()).toBe('dd/MM/yy');
  });

  it('reads from and writes to localStorage', () => {
    localStorage.setItem(DateFormatService.STORAGE_KEY, JSON.stringify({dateFormat: 'YY/MM/DD'}));

    TestBed.configureTestingModule({});
    const service = TestBed.inject(DateFormatService);
    expect(service.state().dateFormat).toBe('YY/MM/DD');
    expect(service.format('2026-04-09')).toBe('26/04/09');

    service.update({dateFormat: 'MM/DD/YY'});
    expect(service.toAngularFormat()).toBe('MM/dd/yy');
    expect(localStorage.getItem(DateFormatService.STORAGE_KEY)).toBe(JSON.stringify({dateFormat: 'MM/DD/YY'}));
  });

  it('avoids browser storage access on the server platform', () => {
    TestBed.configureTestingModule({
      providers: [{provide: PLATFORM_ID, useValue: 'server'}],
    });

    const service = TestBed.inject(DateFormatService);
    expect(service.state().dateFormat).toBe('DD/MM/YY');
    expect(service.format('2026-04-09')).toBe('09/04/26');
  });
});
