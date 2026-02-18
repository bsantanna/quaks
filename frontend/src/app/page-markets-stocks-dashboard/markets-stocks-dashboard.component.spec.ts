import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { MarketsStocksDashboard } from './markets-stocks-dashboard.component';

describe('MarketsStocksEodDashboard', () => {
  let component: MarketsStocksDashboard;
  let fixture: ComponentFixture<MarketsStocksDashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsStocksDashboard],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])]
    }).compileComponents();

    fixture = TestBed.createComponent(MarketsStocksDashboard);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
