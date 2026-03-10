import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InsightsAgents } from './insights-agents';

describe('InsightsAgents', () => {
  let component: InsightsAgents;
  let fixture: ComponentFixture<InsightsAgents>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsAgents]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InsightsAgents);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
