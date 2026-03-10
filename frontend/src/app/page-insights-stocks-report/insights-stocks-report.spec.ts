import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InsightsStocksReport } from './insights-stocks-report';

describe('InsightsStocksReport', () => {
  let component: InsightsStocksReport;
  let fixture: ComponentFixture<InsightsStocksReport>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsStocksReport]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InsightsStocksReport);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
