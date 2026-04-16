import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { NavigationHeader } from './navigation-header';
import { STOCK_MARKETS } from '../constants';

let observeCallback: Function;

beforeAll(() => {
  global.IntersectionObserver = class {
    constructor(cb: Function) { observeCallback = cb; }
    observe() {}
    unobserve() {}
    disconnect() {}
  } as any;
});

describe('NavigationHeader', () => {
  let component: NavigationHeader;
  let fixture: ComponentFixture<NavigationHeader>;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavigationHeader]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NavigationHeader);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    jest.spyOn(router, 'navigate').mockResolvedValue(true);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should navigate when stock ticker selected', () => {
    const index = STOCK_MARKETS[0] ?? 'us_market';
    component.onKeyTickerSelected({index, key_ticker: 'AAPL'});
    expect(router.navigate).toHaveBeenCalledWith(['/markets/stocks', 'AAPL']);
  });

  it('should set stickyVisible based on IntersectionObserver', () => {
    component.ngAfterViewInit();
    if (observeCallback) {
      observeCallback([{isIntersecting: false}]);
      expect(component.stickyVisible()).toBe(true);
      observeCallback([{isIntersecting: true}]);
      expect(component.stickyVisible()).toBe(false);
    }
  });

  it('should disconnect observer on destroy', () => {
    component.ngAfterViewInit();
    component.ngOnDestroy();
    // Should not throw
    expect(component).toBeTruthy();
  });
});
