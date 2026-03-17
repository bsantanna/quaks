import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InsightsFinance } from './insights-finance';

describe('InsightsFinance', () => {
  let component: InsightsFinance;
  let fixture: ComponentFixture<InsightsFinance>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsFinance]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InsightsFinance);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
