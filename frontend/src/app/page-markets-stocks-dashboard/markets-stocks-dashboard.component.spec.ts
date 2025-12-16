import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MarketsStocksDashboard } from './markets-stocks-dashboard.component';

describe('MarketsStocksEodDashboard', () => {
  let component: MarketsStocksDashboard;
  let fixture: ComponentFixture<MarketsStocksDashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsStocksDashboard]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MarketsStocksDashboard);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
