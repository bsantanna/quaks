import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StockComparisonCharts } from './stock-comparison-charts';

describe('StockComparisonCharts', () => {
  let component: StockComparisonCharts;
  let fixture: ComponentFixture<StockComparisonCharts>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockComparisonCharts]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StockComparisonCharts);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
