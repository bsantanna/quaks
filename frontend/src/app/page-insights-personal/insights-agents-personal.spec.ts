import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { AuthService } from '../shared/services/auth.service';
import { InsightsAgentProfileService } from '../shared/services/insights-agent-profile.service';

import { InsightsAgentsPersonal } from './insights-agents-personal';

describe('InsightsAgentsPersonal', () => {
  let component: InsightsAgentsPersonal;
  let fixture: ComponentFixture<InsightsAgentsPersonal>;
  const mockAuthService = {
    isLoggedIn: signal(false),
    initiateLogin: jest.fn(),
  };
  const mockProfile = {type: 'news_analyst', name: 'NA', role: 'Reporter', avatar: '/b.svg', bio: []};
  const mockProfileService = {
    getAgentProfile: jest.fn().mockReturnValue(of(mockProfile)),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsAgentsPersonal],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {provide: AuthService, useValue: mockAuthService},
        {provide: InsightsAgentProfileService, useValue: mockProfileService},
        {provide: ActivatedRoute, useValue: {snapshot: {paramMap: {get: () => 'news-analyst'}}}},
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InsightsAgentsPersonal);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should expose isLoggedIn from auth service', () => {
    expect(component.isLoggedIn()).toBe(false);
  });

  it('should load agent profile based on route param', () => {
    expect(mockProfileService.getAgentProfile).toHaveBeenCalledWith('news-analyst');
    expect(component.agentProfile()).toEqual(mockProfile);
  });
});
