import {ComponentFixture, TestBed} from '@angular/core/testing';
import {StockComparisonCharts} from './stock-comparison-charts';

describe('StockComparisonCharts', () => {
  let component: StockComparisonCharts;
  let fixture: ComponentFixture<StockComparisonCharts>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockComparisonCharts]
    }).compileComponents();

    fixture = TestBed.createComponent(StockComparisonCharts);
    fixture.componentRef.setInput('symbols', []);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should return about:blank when no symbols', () => {
    expect(component.kibanaUrl().toString()).toContain('about:blank');
  });

  it('should build kibana URL with single symbol', () => {
    fixture.componentRef.setInput('symbols', ['AAPL']);
    fixture.detectChanges();
    const url = component.kibanaUrl().toString();
    expect(url).toContain('key_ticker%3AAAPL');
    expect(url).toContain('be7be596-f3e4-4473-8f38-863b42c9b985');
  });

  it('should build kibana URL with OR for multiple symbols', () => {
    fixture.componentRef.setInput('symbols', ['AAPL', 'MSFT', 'GOOGL']);
    fixture.detectChanges();
    const url = component.kibanaUrl().toString();
    expect(url).toContain('key_ticker%3AAAPL');
    expect(url).toContain('OR');
    expect(url).toContain('key_ticker%3AMSFT');
    expect(url).toContain('key_ticker%3AGOOGL');
  });

  it('should use dashboards endpoint', () => {
    fixture.componentRef.setInput('symbols', ['AAPL']);
    fixture.detectChanges();
    const url = component.kibanaUrl().toString();
    expect(url).toContain('/app/dashboards');
    expect(url).toContain('#/view/');
  });

  it('should include embed parameters', () => {
    fixture.componentRef.setInput('symbols', ['AAPL']);
    fixture.detectChanges();
    const url = component.kibanaUrl().toString();
    expect(url).toContain('embed=true');
    expect(url).toContain('hide-filter-bar=true');
  });

  it('should use custom intervalInDays in time range', () => {
    fixture.componentRef.setInput('symbols', ['AAPL']);
    fixture.componentRef.setInput('intervalInDays', 90);
    fixture.detectChanges();
    const url = component.kibanaUrl().toString();
    expect(url).toContain('now-90d');
  });

  it('should handle iframe load without error', () => {
    const mockIframe = {
      contentDocument: {
        createElement: jest.fn().mockReturnValue({innerHTML: ''}),
        head: {appendChild: jest.fn()},
      },
    } as unknown as HTMLIFrameElement;
    expect(() => component.onIframeLoad(mockIframe)).not.toThrow();
  });

  it('should fallback to contentWindow.document when contentDocument is null', () => {
    const appendChildFn = jest.fn();
    const mockIframe = {
      contentDocument: null,
      contentWindow: {
        document: {
          createElement: jest.fn().mockReturnValue({innerHTML: ''}),
          head: {appendChild: appendChildFn},
        },
      },
    } as unknown as HTMLIFrameElement;
    component.onIframeLoad(mockIframe);
    expect(appendChildFn).toHaveBeenCalled();
  });

  it('should handle iframe with no document available', () => {
    const mockIframe = {
      contentDocument: null,
      contentWindow: {document: null},
    } as unknown as HTMLIFrameElement;
    expect(() => component.onIframeLoad(mockIframe)).not.toThrow();
  });

  it('should handle iframe load error gracefully', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    const mockIframe = {
      get contentDocument() { throw new Error('cross-origin'); },
      contentWindow: null,
    } as unknown as HTMLIFrameElement;
    component.onIframeLoad(mockIframe);
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});
