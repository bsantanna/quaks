import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';

import { InsightsAgents } from './insights-agents';
import { InsightsAgentProfileService } from '../shared/services/insights-agent-profile.service';

describe('InsightsAgents', () => {
  let component: InsightsAgents;
  let fixture: ComponentFixture<InsightsAgents>;
  const mockProfiles = [
    {type: 'financial_analyst', name: 'FA', role: 'Analyst', avatar: '/a.svg', bio: []},
    {type: 'news_analyst', name: 'NA', role: 'Reporter', avatar: '/b.svg', bio: []},
  ];
  const mockProfileService = {
    getAllAgentProfiles: jest.fn().mockReturnValue(of(mockProfiles)),
    getAgentProfile: jest.fn(),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsAgents],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {provide: InsightsAgentProfileService, useValue: mockProfileService},
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

  it('should load agent profiles on init in browser', () => {
    expect(mockProfileService.getAllAgentProfiles).toHaveBeenCalled();
    expect(component.agents().length).toBe(2);
  });

  it('should handle single word agent type', () => {
    expect(component.agentSlug({type: 'simple'} as any)).toBe('simple');
  });
});
