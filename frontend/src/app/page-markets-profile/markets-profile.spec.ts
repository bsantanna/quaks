import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';
import { BehaviorSubject } from 'rxjs';
import { of } from 'rxjs';

import { MarketsProfile } from './markets-profile';
import { SeoService } from '../shared/services/seo.service';
import { MarketsStatsService } from '../shared/services/markets-stats.service';
import { IndexedKeyTickerService } from '../shared/services/indexed-key-ticker.service';

describe('MarketsProfile', () => {
  let component: MarketsProfile;
  let fixture: ComponentFixture<MarketsProfile>;
  let httpTesting: HttpTestingController;
  const mockSeoService = {
    update: jest.fn(),
    reset: jest.fn(),
  };
  const paramMap$ = new BehaviorSubject({get: (key: string) => key === 'keyTicker' ? 'AAPL' : null} as any);
  const mockStatsService = {
    getCompanyProfile: jest.fn().mockReturnValue(of({
      key_ticker: 'AAPL',
      name: 'Apple Inc',
      description: 'Technology company',
    })),
  };
  const mockIndexedService = {
    findKeyTicker: jest.fn().mockReturnValue({index: 'us_market', key_ticker: 'AAPL'}),
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    await TestBed.configureTestingModule({
      imports: [MarketsProfile],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {provide: SeoService, useValue: mockSeoService},
        {provide: MarketsStatsService, useValue: mockStatsService},
        {provide: IndexedKeyTickerService, useValue: mockIndexedService},
        {provide: ActivatedRoute, useValue: {paramMap: paramMap$.asObservable()}},
      ]
    })
    .compileComponents();

    httpTesting = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(MarketsProfile);
    component = fixture.componentInstance;
    fixture.detectChanges();

    // Flush the company_descriptions.json request
    const descReqs = httpTesting.match('/json/company_descriptions.json');
    descReqs.forEach(r => r.flush({}));

    await fixture.whenStable();
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should format large numbers', () => {
    expect(component.formatLargeNumber(1_500_000_000_000)).toBe('1.50T');
    expect(component.formatLargeNumber(2_300_000_000)).toBe('2.30B');
    expect(component.formatLargeNumber(45_000_000)).toBe('45.00M');
    expect(component.formatLargeNumber(1_500)).toBe('1.5K');
    expect(component.formatLargeNumber(null)).toBe('--');
  });

  it('should format negative large numbers', () => {
    expect(component.formatLargeNumber(-2_500_000_000)).toBe('-2.50B');
  });

  it('should format small numbers below 1K', () => {
    expect(component.formatLargeNumber(500)).toBe('500.00');
    expect(component.formatLargeNumber(undefined)).toBe('--');
  });

  it('should format percentages', () => {
    expect(component.formatPercent(0.2534)).toBe('25.34%');
    expect(component.formatPercent(-0.05)).toBe('-5.00%');
    expect(component.formatPercent(null)).toBe('--');
  });

  it('should format numbers with custom decimals', () => {
    expect(component.formatNumber(3.14159, 3)).toBe('3.142');
    expect(component.formatNumber(null)).toBe('--');
    expect(component.formatNumber(undefined)).toBe('--');
  });

  it('should format dates', () => {
    expect(component.formatDate('2025-03-15')).toBe('15/03/25');
    expect(component.formatDate(null)).toBe('--');
    expect(component.formatDate(undefined)).toBe('--');
  });

  it('should reset seo on destroy', () => {
    component.ngOnDestroy();
    expect(mockSeoService.reset).toHaveBeenCalled();
  });

  it('should read keyTicker from route params', () => {
    expect(component.keyTicker()).toBe('AAPL');
  });

  it('should compute indexName from keyTicker', () => {
    expect(component.indexName()).toContain('quaks_stocks-metadata_');
  });

  it('should compute exchangeFlag', () => {
    const flag = component.exchangeFlag();
    expect(typeof flag).toBe('string');
  });

  it('should load profile data via effect', () => {
    expect(mockStatsService.getCompanyProfile).toHaveBeenCalled();
    expect(component.profile()).toBeTruthy();
    expect(component.profile()!.name).toBe('Apple Inc');
    expect(component.loading()).toBe(false);
  });

  it('should use profile description as companyAbout fallback', () => {
    const about = component.companyAbout();
    expect(about).toBe('Technology company');
  });

  it('should update SEO on profile load', () => {
    expect(mockSeoService.update).toHaveBeenCalledWith(
      expect.objectContaining({
        title: expect.stringContaining('AAPL'),
        path: '/markets/profile/AAPL',
      })
    );
  });
});
