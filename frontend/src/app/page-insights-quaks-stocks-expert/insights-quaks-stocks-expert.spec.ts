import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InsightsQuaksStocksExpert } from './insights-quaks-stocks-expert';

describe('InsightsQuaksStocksExpert', () => {
  let component: InsightsQuaksStocksExpert;
  let fixture: ComponentFixture<InsightsQuaksStocksExpert>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsQuaksStocksExpert]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InsightsQuaksStocksExpert);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
