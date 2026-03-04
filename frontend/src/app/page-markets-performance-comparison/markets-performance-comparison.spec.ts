import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, convertToParamMap } from '@angular/router';
import { BehaviorSubject } from 'rxjs';

import { MarketsPerformanceComparison } from './markets-performance-comparison';

describe('MarketsPerformanceComparison', () => {
  let component: MarketsPerformanceComparison;
  let fixture: ComponentFixture<MarketsPerformanceComparison>;
  let queryParamMap$: BehaviorSubject<any>;
  let mockRouter: { navigate: jest.Mock };

  beforeEach(async () => {
    queryParamMap$ = new BehaviorSubject(convertToParamMap({}));
    mockRouter = { navigate: jest.fn().mockResolvedValue(true) };

    await TestBed.configureTestingModule({
      imports: [MarketsPerformanceComparison],
      providers: [
        { provide: ActivatedRoute, useValue: { queryParamMap: queryParamMap$.asObservable() } },
        { provide: Router, useValue: mockRouter },
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MarketsPerformanceComparison);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should parse symbols from query param', () => {
    queryParamMap$.next(convertToParamMap({ q: 'AAPL,MSFT,GOOGL' }));
    expect(component.symbols()).toEqual(['AAPL', 'MSFT', 'GOOGL']);
  });

  it('should handle empty query param', () => {
    queryParamMap$.next(convertToParamMap({}));
    expect(component.symbols()).toEqual([]);
  });

  it('should trim whitespace from symbols', () => {
    queryParamMap$.next(convertToParamMap({ q: ' AAPL , MSFT ' }));
    expect(component.symbols()).toEqual(['AAPL', 'MSFT']);
  });

  it('should filter out empty strings', () => {
    queryParamMap$.next(convertToParamMap({ q: 'AAPL,,MSFT,' }));
    expect(component.symbols()).toEqual(['AAPL', 'MSFT']);
  });

  it('should handle single symbol', () => {
    queryParamMap$.next(convertToParamMap({ q: 'AAPL' }));
    expect(component.symbols()).toEqual(['AAPL']);
  });

  it('should navigate with updated query params on updateSymbols', () => {
    component.updateSymbols(['TSLA', 'AMZN']);
    expect(mockRouter.navigate).toHaveBeenCalledWith([], {
      relativeTo: expect.anything(),
      queryParams: { q: 'TSLA,AMZN' },
      queryParamsHandling: 'replace',
    });
  });

  it('should unsubscribe on destroy', () => {
    expect(() => component.ngOnDestroy()).not.toThrow();
  });
});
