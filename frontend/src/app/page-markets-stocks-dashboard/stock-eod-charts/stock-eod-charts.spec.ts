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
    fixture.componentRef.setInput('intervalInDates', '2024-01-01,2024-12-31');
    fixture.componentRef.setInput('useIntervalInDates', false);
    fixture.componentRef.setInput('intervalInDays', 30);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
