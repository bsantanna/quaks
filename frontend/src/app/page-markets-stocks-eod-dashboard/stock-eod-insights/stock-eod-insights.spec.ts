import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StockEodInsights } from './stock-eod-insights';

describe('StockEodInsights', () => {
  let component: StockEodInsights;
  let fixture: ComponentFixture<StockEodInsights>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockEodInsights]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StockEodInsights);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
