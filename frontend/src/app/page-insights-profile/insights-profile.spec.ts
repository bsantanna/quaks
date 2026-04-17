import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { InsightsProfile } from './insights-profile';
import { InsightsAgentProfileService } from '../shared/services/insights-agent-profile.service';

describe('InsightsProfile', () => {
  let component: InsightsProfile;
  let fixture: ComponentFixture<InsightsProfile>;
  const mockProfile = {type: 'macro_research', name: 'MR', role: 'Researcher', avatar: '/c.svg', bio: ['Bio text']};
  const mockProfileService = {
    getAgentProfile: jest.fn().mockReturnValue(of(mockProfile)),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsProfile],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {provide: InsightsAgentProfileService, useValue: mockProfileService},
        {provide: ActivatedRoute, useValue: {snapshot: {paramMap: {get: () => 'macro-research'}}}},
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InsightsProfile);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('converts agent type underscores to hyphens via agentSlug', () => {
    expect(component.agentSlug({type: 'macro_research'} as any)).toBe('macro-research');
  });

  it('should load profile from route param', () => {
    expect(mockProfileService.getAgentProfile).toHaveBeenCalledWith('macro-research');
    expect(component.profile()).toEqual(mockProfile);
  });
});
