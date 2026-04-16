import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { InsightsAgents } from './insights-agents';

describe('InsightsAgents', () => {
  let component: InsightsAgents;
  let fixture: ComponentFixture<InsightsAgents>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsAgents],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InsightsAgents);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('converts agent type underscores to hyphens via agentSlug', () => {
    expect(component.agentSlug({type: 'financial_analyst'} as any)).toBe('financial-analyst');
    expect(component.agentSlug({type: 'no_underscores_here'} as any)).toBe('no-underscores-here');
  });
});
