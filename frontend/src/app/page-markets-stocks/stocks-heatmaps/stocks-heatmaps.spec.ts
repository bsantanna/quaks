import {ComponentFixture, TestBed} from '@angular/core/testing';
import {of} from 'rxjs';
import {ActivatedRoute, Router} from '@angular/router';

import {StocksHeatmaps} from './stocks-heatmaps';
import {HttpClient} from '@angular/common/http';
import {MarketsStatsService, ShareUrlService} from '../../shared';

describe('StocksHeatmaps', () => {
  let component: StocksHeatmaps;
  let fixture: ComponentFixture<StocksHeatmaps>;
  const httpClient = {
    get: jest.fn(),
  };
  const statsService = {
    getStatsCloseBulk: jest.fn(),
    getMarketCapsBulk: jest.fn(),
  };
  const router = {
    navigate: jest.fn(),
  };
  const shareUrlService = {
    update: jest.fn(),
  };
  const constituents = [
    {ticker: 'AAPL', name: 'Apple', sector: 'Tech', industry: 'Hardware'},
    {ticker: 'MSFT', name: 'Microsoft', sector: 'Tech', industry: 'Software'},
  ];

  beforeEach(async () => {
    jest.clearAllMocks();
    httpClient.get.mockReturnValue(of(constituents));
    statsService.getStatsCloseBulk.mockReturnValue(of({
      items: [{
        key_ticker: 'AAPL',
        most_recent_close: 10,
        most_recent_date: '2026-04-09',
        most_recent_low: 9,
        most_recent_high: 11,
        most_recent_volume: 100,
        most_recent_open: 10,
        percent_variance: 2,
      }],
    }));
    statsService.getMarketCapsBulk.mockReturnValue(of({
      items: [
        {key_ticker: 'AAPL', market_capitalization: 100},
        {key_ticker: 'MSFT', market_capitalization: 90},
      ],
    }));

    await TestBed.configureTestingModule({
      imports: [StocksHeatmaps],
      providers: [
        {provide: HttpClient, useValue: httpClient},
        {provide: MarketsStatsService, useValue: statsService},
        {provide: Router, useValue: router},
        {provide: ShareUrlService, useValue: shareUrlService},
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              queryParamMap: {
                get: jest.fn().mockReturnValue('2026-04-09'),
              },
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(StocksHeatmaps);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default to sp500 index', () => {
    expect(component.selectedIndex()).toBe('sp500');
  });

  it('should toggle zoom on sector', () => {
    component.toggleZoom('Technology');
    expect(component.zoomedSector()).toBe('Technology');

    component.toggleZoom('Technology');
    expect(component.zoomedSector()).toBeNull();
  });

  it('should zoom out', () => {
    component.toggleZoom('Technology');
    component.zoomOut();
    expect(component.zoomedSector()).toBeNull();
  });

  it('should return correct tile color for positive variance', () => {
    const color = component.tileColor(3.0);
    expect(color).toMatch(/^rgb\(\d+,\d+,\d+\)$/);
    // Green should dominate
    const match = color.match(/rgb\((\d+),(\d+),(\d+)\)/);
    expect(Number(match![2])).toBeGreaterThan(Number(match![1]));
  });

  it('should return correct tile color for negative variance', () => {
    const color = component.tileColor(-3.0);
    const match = color.match(/rgb\((\d+),(\d+),(\d+)\)/);
    // Red should dominate
    expect(Number(match![1])).toBeGreaterThan(Number(match![2]));
  });

  it('should return neutral color for zero variance', () => {
    expect(component.tileColor(0)).toBe('#2a2e39');
  });

  it('loads heatmap data and updates share metadata', () => {
    expect(httpClient.get).toHaveBeenCalledWith('/json/heatmap_sp500.json');
    expect(statsService.getStatsCloseBulk).toHaveBeenCalledWith(
      'quaks_stocks-eod_latest',
      ['AAPL', 'MSFT'],
      '2026-04-02',
      '2026-04-09',
    );
    expect(component.loading()).toBe(false);
    expect(component.heatmapDate()).toBe('2026-04-09');
    expect(component.sectorGroups().length).toBeGreaterThan(0);
    expect(shareUrlService.update).toHaveBeenCalled();
  });

  it('switches index and navigates to a stock page', () => {
    component.zoomedSector.set('Technology');

    component.switchIndex('nasdaq100');
    component.navigateToStock('AAPL');

    expect(component.selectedIndex()).toBe('nasdaq100');
    expect(component.zoomedSector()).toBeNull();
    expect(httpClient.get).toHaveBeenLastCalledWith('/json/heatmap_nasdaq100.json');
    expect(router.navigate).toHaveBeenCalledWith(['/markets/stocks', 'AAPL']);
  });

  it('tracks mouse movement relative to the heatmap container', () => {
    const container = fixture.nativeElement.querySelector('.heatmap-container') as HTMLElement;
    jest.spyOn(container, 'getBoundingClientRect').mockReturnValue({
      x: 0,
      y: 0,
      width: 100,
      height: 50,
      top: 5,
      left: 7,
      bottom: 55,
      right: 107,
      toJSON: () => ({}),
    });

    component.onMouseMove({clientX: 10, clientY: 20} as MouseEvent);
    expect(component.mouseX()).toBe(3);
    expect(component.mouseY()).toBe(15);
  });

  it('resets share state on destroy', () => {
    component.ngOnDestroy();
    expect(shareUrlService.update).toHaveBeenLastCalledWith({title: '', url: ''});
  });
});
