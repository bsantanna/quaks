import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InsightsStocks } from './insights-stocks';

describe('InsightsStocks', () => {
  let component: InsightsStocks;
  let fixture: ComponentFixture<InsightsStocks>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsStocks]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InsightsStocks);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
