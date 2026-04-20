import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { of } from 'rxjs';

import { InsightsAgents } from './insights-agents';
import { InsightsAgentProfileService } from '../shared/services/insights-agent-profile.service';
import { PersonalAgentService } from '../shared/services/personal-agent.service';
import { AuthService } from '../shared/services/auth.service';

describe('InsightsAgents', () => {
  let component: InsightsAgents;
  let fixture: ComponentFixture<InsightsAgents>;
  const mockProfiles = [
    {type: 'financial_analyst', name: 'FA', role: 'Analyst', avatar: '/a.svg', bio: []},
    {type: 'news_analyst', name: 'NA', role: 'Reporter', avatar: '/b.svg', bio: []},
  ];
  const mockPersonalAgents = [
    {id: '1', is_active: true, created_at: '', agent_name: 'mine', agent_type: 'news_analyst', agent_summary: '', language_model_id: null},
  ];
  let mockProfileService: { getAllAgentProfiles: jest.Mock; getAgentProfile: jest.Mock };
  let mockPersonalService: { list: jest.Mock };
  let mockAuthService: { isLoggedIn: ReturnType<typeof signal<boolean>> };

  const setupComponent = async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsAgents],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {provide: InsightsAgentProfileService, useValue: mockProfileService},
        {provide: PersonalAgentService, useValue: mockPersonalService},
        {provide: AuthService, useValue: mockAuthService},
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InsightsAgents);
    component = fixture.componentInstance;
    await fixture.whenStable();
    fixture.detectChanges();
  };

  beforeEach(() => {
    mockProfileService = {
      getAllAgentProfiles: jest.fn().mockReturnValue(of(mockProfiles)),
      getAgentProfile: jest.fn(),
    };
    mockPersonalService = {
      list: jest.fn().mockReturnValue(of(mockPersonalAgents)),
    };
    mockAuthService = {
      isLoggedIn: signal(true),
    };
  });

  it('should create', async () => {
    await setupComponent();
    expect(component).toBeTruthy();
  });

  it('converts agent type underscores to hyphens via agentSlug', async () => {
    await setupComponent();
    expect(component.agentSlug({type: 'financial_analyst'} as any)).toBe('financial-analyst');
    expect(component.agentSlug({type: 'no_underscores_here'} as any)).toBe('no-underscores-here');
  });

  it('should load agent profiles on init in browser', async () => {
    await setupComponent();
    expect(mockProfileService.getAllAgentProfiles).toHaveBeenCalled();
    expect(component.agents().length).toBe(2);
  });

  it('should handle single word agent type', async () => {
    await setupComponent();
    expect(component.agentSlug({type: 'simple'} as any)).toBe('simple');
  });

  it('flags configured personal agents via hasPersonal when logged in', async () => {
    await setupComponent();
    expect(mockPersonalService.list).toHaveBeenCalled();
    expect(component.hasPersonal(mockProfiles[0])).toBe(false);
    expect(component.hasPersonal(mockProfiles[1])).toBe(true);
  });

  it('renders the Configured badge only on configured cards', async () => {
    await setupComponent();
    const badges = fixture.nativeElement.querySelectorAll('.agent-badge');
    expect(badges.length).toBe(1);
    expect(badges[0].textContent.trim()).toBe('Configured');
  });

  it('does not fetch personal agents when logged out', async () => {
    mockAuthService.isLoggedIn = signal(false);
    await setupComponent();
    expect(mockPersonalService.list).not.toHaveBeenCalled();
    expect(component.hasPersonal(mockProfiles[0])).toBe(false);
    expect(component.hasPersonal(mockProfiles[1])).toBe(false);
    const badges = fixture.nativeElement.querySelectorAll('.agent-badge');
    expect(badges.length).toBe(0);
  });
});
