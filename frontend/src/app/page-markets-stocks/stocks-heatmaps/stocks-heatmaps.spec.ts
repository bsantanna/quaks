import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {provideHttpClient} from '@angular/common/http';
import {provideRouter} from '@angular/router';

import {StocksHeatmaps} from './stocks-heatmaps';

describe('StocksHeatmaps', () => {
  let component: StocksHeatmaps;
  let fixture: ComponentFixture<StocksHeatmaps>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StocksHeatmaps],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(StocksHeatmaps);
    component = fixture.componentInstance;
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
});
