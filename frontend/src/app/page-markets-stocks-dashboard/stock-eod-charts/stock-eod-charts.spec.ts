import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StockEodCharts } from './stock-eod-charts';

describe('StockEodCharts', () => {
  let component: StockEodCharts;
  let fixture: ComponentFixture<StockEodCharts>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockEodCharts]
    }).compileComponents();

    fixture = TestBed.createComponent(StockEodCharts);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('keyTicker', 'AAPL');
    fixture.componentRef.setInput('intervalInDates', '2024-01-01_2024-12-31');
    fixture.componentRef.setInput('useIntervalInDates', false);
    fixture.componentRef.setInput('intervalInDays', 30);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default to stock_price tab', () => {
    expect(component.selectedTab()).toBe('stock_price');
  });

  it('should generate kibana URL for default tab', () => {
    const url = component.kibanaUrl();
    expect(url).toBeTruthy();
  });

  it('should generate different URLs for each indicator tab', () => {
    const tabs = [
      'indicator_ema', 'indicator_ad', 'indicator_adx', 'indicator_cci',
      'indicator_macd', 'indicator_obv', 'indicator_rsi', 'indicator_stoch',
    ];
    const urls = new Set<string>();
    for (const tab of tabs) {
      component.selectedTab.set(tab);
      urls.add(String(component.kibanaUrl()));
    }
    expect(urls.size).toBe(tabs.length);
  });

  it('should use intervalInDates when useIntervalInDates is true', () => {
    fixture.componentRef.setInput('useIntervalInDates', true);
    fixture.componentRef.setInput('intervalInDates', '2024-01-01_2024-12-31');
    fixture.detectChanges();
    const url = String(component.kibanaUrl());
    expect(url).toContain('2024-01-01');
  });

  it('should use intervalInDays when useIntervalInDates is false', () => {
    fixture.componentRef.setInput('useIntervalInDates', false);
    fixture.componentRef.setInput('intervalInDays', 90);
    fixture.detectChanges();
    const url = String(component.kibanaUrl());
    expect(url).toContain('now-90d');
  });

  it('should handle onIframeLoad without error when cross-origin', () => {
    const iframe = {contentDocument: null, contentWindow: null} as any;
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    component.onIframeLoad(iframe);
    consoleSpy.mockRestore();
    // Should not throw
    expect(component).toBeTruthy();
  });
});
