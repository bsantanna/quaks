import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StockEodCharts } from './stock-eod-charts';

describe('StockEodCharts', () => {
  let component: StockEodCharts;
  let fixture: ComponentFixture<StockEodCharts>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockEodCharts]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StockEodCharts);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
