import { ComponentFixture, TestBed } from '@angular/core/testing';
import {ActivatedRoute, convertToParamMap} from '@angular/router';
import { of, throwError } from 'rxjs';

import { InsightsPreview } from './insights-preview';
import {DateFormatService, SeoService, ShareUrlService} from '../shared';
import {IndexedKeyTickerService} from '../shared/services/indexed-key-ticker.service';
import {MarketsInsightsService} from '../shared/services/markets-insights.service';

describe('InsightsPreview', () => {
  let component: InsightsPreview;
  let fixture: ComponentFixture<InsightsPreview>;
  const insightsService = {
    getInsightsPreview: jest.fn(),
    cancelInsightsPreview: jest.fn(),
  };
  const tickerService = {
    indexedKeyTickers: jest.fn().mockReturnValue([{key_ticker: 'AAPL'}]),
  };
  const shareUrlService = {
    update: jest.fn(),
  };
  const seoService = {
    update: jest.fn(),
    reset: jest.fn(),
  };
  const dateFormatService = {
    format: jest.fn((value: string) => `formatted:${value}`),
  };
  const previewItem = {
    doc_id: 'doc-1',
    executive_summary: 'Preview summary',
    report_html: 'Title<br>(AAPL)',
    skill_name: '/macro_research',
    author_username: 'analyst',
    date_timestamp: '2026-04-09T12:00:00Z',
    status: 'pending' as const,
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    insightsService.getInsightsPreview.mockReturnValue(of({...previewItem}));
    insightsService.cancelInsightsPreview.mockReturnValue(of(void 0));
    jest.spyOn(window, 'print').mockImplementation(() => undefined);

    await TestBed.configureTestingModule({
      imports: [InsightsPreview],
      providers: [
        {provide: ActivatedRoute, useValue: {paramMap: of(convertToParamMap({docId: 'doc-1'}))}},
        {provide: MarketsInsightsService, useValue: insightsService},
        {provide: IndexedKeyTickerService, useValue: tickerService},
        {provide: ShareUrlService, useValue: shareUrlService},
        {provide: SeoService, useValue: seoService},
        {provide: DateFormatService, useValue: dateFormatService},
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InsightsPreview);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('loads the preview and updates share/seo metadata', () => {
    expect(insightsService.getInsightsPreview).toHaveBeenCalledWith('doc-1');
    expect(component.loading()).toBe(false);
    expect(component.item()?.report_html).toContain('ticker-link');
    expect(shareUrlService.update).toHaveBeenCalledWith({
      title: 'Preview summary',
      url: 'http://localhost/insights/preview/doc-1',
    });
    expect(seoService.update).toHaveBeenCalledWith({
      title: 'Preview summary',
      path: '/insights/preview/doc-1',
    });
  });

  it('cancels and refreshes the document on success', () => {
    component.cancelDocument();

    expect(component.cancelling()).toBe(false);
    expect(component.cancelError()).toBe(false);
    expect(insightsService.cancelInsightsPreview).toHaveBeenCalledWith('doc-1');
    expect(insightsService.getInsightsPreview).toHaveBeenCalledTimes(2);
  });

  it('marks cancel errors when the cancel request fails', () => {
    insightsService.cancelInsightsPreview.mockReturnValueOnce(throwError(() => new Error('boom')));

    component.cancelDocument();

    expect(component.cancelError()).toBe(true);
    expect(component.cancelling()).toBe(false);
  });

  it('adds and cleans up print styles when downloading pdf', () => {
    component.downloadPdf();
    expect(document.getElementById('quaks-print-style')).toBeTruthy();
    expect(window.print).toHaveBeenCalled();

    window.dispatchEvent(new Event('afterprint'));
    expect(document.getElementById('quaks-print-style')).toBeNull();
  });

  it('formats labels and resets metadata on destroy', () => {
    expect(component.statusLabel('pending')).toBe('Pending Review');
    expect(component.statusLabel('processed')).toBe('Published');
    expect(component.statusLabel('cancelled')).toBe('Cancelled');
    expect(component.statusLabel('custom')).toBe('custom');
    expect(component.agentAvatarSrc('/macro_research')).toBe('/svg/insights-agent_quaks-macro-research.svg');
    expect(component.formatDate('2026-04-09T12:00:00Z')).toBe('formatted:2026-04-09');

    component.ngOnDestroy();
    expect(shareUrlService.update).toHaveBeenLastCalledWith({title: '', url: ''});
    expect(seoService.reset).toHaveBeenCalled();
  });
});
