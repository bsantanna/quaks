import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {ActivatedRoute, Router} from '@angular/router';
import {signal} from '@angular/core';
import {of, throwError} from 'rxjs';

import {AuthService} from '../shared/services/auth.service';
import {InsightsAgentProfileService} from '../shared/services/insights-agent-profile.service';
import {PersonalAgentService} from '../shared/services/personal-agent.service';
import {FeedbackMessageService, SeoService} from '../shared';
import {InsightsAgentsPersonal} from './insights-agents-personal';

describe('InsightsAgentsPersonal wizard', () => {
  const mockProfile = {
    type: 'quaks_news_analyst',
    name: 'News Analyst',
    role: 'Reporter',
    avatar: '/a.svg',
    bio: [],
  };

  function buildTestBed(options: {
    slug?: string;
    isLoggedIn?: boolean;
    tier?: 'free' | 'pro';
    existingAgents?: any[];
    expanded?: any;
    create?: any;
    resetSettings?: any;
    update?: any;
    updateSetting?: any;
    deleteError?: boolean;
  } = {}) {
    const authService = {
      isLoggedIn: signal(options.isLoggedIn ?? true),
      subscriptionTier: signal(options.tier ?? 'free'),
      initiateLogin: jest.fn(),
    };

    const profileService = {
      getAgentProfile: jest.fn().mockReturnValue(of(mockProfile)),
    };

    const agentService = {
      list: jest.fn().mockReturnValue(of(options.existingAgents ?? [])),
      getById: jest.fn().mockReturnValue(of(options.expanded ?? {
        id: 'a1',
        is_active: true,
        created_at: '2026-04-20T00:00:00Z',
        agent_name: 'existing-agent',
        agent_type: mockProfile.type,
        agent_summary: 'Before',
        language_model_id: null,
        ag_settings: [{setting_key: 'prompt', setting_value: 'before'}],
      })),
      create: jest.fn().mockReturnValue(of(options.create ?? {
        id: 'a1',
        is_active: true,
        created_at: '2026-04-20T00:00:00Z',
        agent_name: 'new-agent',
        agent_type: mockProfile.type,
        agent_summary: '',
        language_model_id: null,
      })),
      update: jest.fn().mockReturnValue(of(options.update ?? {id: 'a1'})),
      updateSetting: jest.fn().mockReturnValue(of(options.updateSetting ?? {})),
      delete: jest.fn().mockReturnValue(
        options.deleteError
          ? throwError(() => ({error: {detail: 'delete failed'}}))
          : of(undefined),
      ),
      resetSettings: jest.fn().mockReturnValue(of(options.resetSettings ?? {
        id: 'a1',
        is_active: true,
        created_at: '2026-04-20T00:00:00Z',
        agent_name: 'existing-agent',
        agent_type: mockProfile.type,
        agent_summary: '',
        language_model_id: null,
        ag_settings: [{setting_key: 'prompt', setting_value: 'factory-default'}],
      })),
    };

    const feedback = {update: jest.fn()};
    const seo = {update: jest.fn()};
    const router = {navigate: jest.fn()};

    TestBed.configureTestingModule({
      imports: [InsightsAgentsPersonal],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {provide: AuthService, useValue: authService},
        {provide: InsightsAgentProfileService, useValue: profileService},
        {provide: PersonalAgentService, useValue: agentService},
        {provide: FeedbackMessageService, useValue: feedback},
        {provide: SeoService, useValue: seo},
        {provide: Router, useValue: router},
        {
          provide: ActivatedRoute,
          useValue: {snapshot: {paramMap: {get: () => options.slug ?? 'quaks-news-analyst'}}},
        },
      ],
    });

    return {authService, profileService, agentService, feedback, router};
  }

  async function createFixture(
    options: Parameters<typeof buildTestBed>[0] = {},
  ): Promise<{fixture: ComponentFixture<InsightsAgentsPersonal>; component: InsightsAgentsPersonal; mocks: ReturnType<typeof buildTestBed>}> {
    const mocks = buildTestBed(options);
    await TestBed.compileComponents();
    const fixture = TestBed.createComponent(InsightsAgentsPersonal);
    const component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    return {fixture, component, mocks};
  }

  afterEach(() => {
    TestBed.resetTestingModule();
  });

  it('starts at step 1 when no agent of this type exists', async () => {
    const {component} = await createFixture();
    expect(component.currentStep()).toBe(1);
    expect(component.loadState()).toBe('ready');
    expect(component.agentProfile()?.type).toBe('quaks_news_analyst');
  });

  it('skips to step 2 when an agent of this type already exists', async () => {
    const {component, mocks} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
    });
    expect(component.currentStep()).toBe(2);
    expect(mocks.agentService.getById).toHaveBeenCalledWith('a1');
    expect(component.existingAgent()?.agent_name).toBe('existing-agent');
    expect(component.editDraft().settings).toEqual([{key: 'prompt', value: 'before'}]);
  });

  it('renumbers progress steps when resuming an existing agent', async () => {
    const {component} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
    });
    expect(component.mode()).toBe('edit');
    expect(component.visibleSteps().map(s => ({id: s.id, displayId: s.displayId}))).toEqual([
      {id: 2, displayId: 1},
      {id: 3, displayId: 2},
      {id: 4, displayId: 3},
    ]);
  });

  it('keeps all 4 progress steps in create mode', async () => {
    const {component} = await createFixture();
    expect(component.mode()).toBe('create');
    expect(component.visibleSteps().map(s => s.displayId)).toEqual([1, 2, 3, 4]);
  });

  it('rejects invalid name on create', async () => {
    const {component, mocks} = await createFixture();
    component.createName.set('invalid name!');
    component.submitCreate();
    expect(mocks.agentService.create).not.toHaveBeenCalled();
    expect(component.createNameError()).toContain('letters');
  });

  it('creates agent and advances to step 2', async () => {
    const {component, mocks} = await createFixture();
    component.createName.set('my-news-analyst');
    component.submitCreate();
    expect(mocks.agentService.create).toHaveBeenCalledWith({
      agent_name: 'my-news-analyst',
      agent_type: mockProfile.type,
    });
    expect(component.currentStep()).toBe(2);
    expect(component.existingAgent()?.agent_name).toBe('existing-agent');
  });

  it('builds review summary from current draft', async () => {
    const {component} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
    });
    component.updateEditSummary('After');
    component.updateSettingValue('prompt', 'after');
    expect(component.reviewSummary()).toEqual([
      {label: 'Description', value: 'After'},
      {label: 'prompt', value: 'after'},
    ]);
  });

  it('reset-to-defaults reloads factory settings', async () => {
    const {component, mocks} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
    });
    component.resetToFactory();
    expect(mocks.agentService.resetSettings).toHaveBeenCalledWith('a1');
    expect(component.editDraft().settings).toEqual([{key: 'prompt', value: 'factory-default'}]);
  });

  it('requestResetToFactory opens the confirmation dialog without calling the service', async () => {
    const {component, mocks} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
    });
    component.requestResetToFactory();
    expect(component.showResetConfirmation()).toBe(true);
    expect(mocks.agentService.resetSettings).not.toHaveBeenCalled();
  });

  it('cancelResetToFactory closes the dialog without resetting', async () => {
    const {component, mocks} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
    });
    component.requestResetToFactory();
    component.cancelResetToFactory();
    expect(component.showResetConfirmation()).toBe(false);
    expect(mocks.agentService.resetSettings).not.toHaveBeenCalled();
  });

  it('confirmResetToFactory closes the dialog and triggers the reset', async () => {
    const {component, mocks} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
    });
    component.requestResetToFactory();
    component.confirmResetToFactory();
    expect(component.showResetConfirmation()).toBe(false);
    expect(mocks.agentService.resetSettings).toHaveBeenCalledWith('a1');
  });

  it('submit persists only changed settings and moves to step 4', async () => {
    const {component, mocks} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
    });
    component.updateSettingValue('prompt', 'updated');
    component.proceedFromEdit();
    expect(component.currentStep()).toBe(3);
    component.submitConfirmation();
    expect(mocks.agentService.update).toHaveBeenCalled();
    expect(mocks.agentService.updateSetting).toHaveBeenCalledWith({
      agent_id: 'a1',
      setting_key: 'prompt',
      setting_value: 'updated',
    });
    expect(component.currentStep()).toBe(4);
  });

  it('surfaces login-required when not logged in', async () => {
    const {component} = await createFixture({isLoggedIn: false});
    expect(component.isLoggedIn()).toBe(false);
  });

  it('sets error state when profile load fails', async () => {
    const mocks = buildTestBed();
    mocks.profileService.getAgentProfile.mockReturnValue(throwError(() => new Error('nope')));
    await TestBed.compileComponents();
    const fixture = TestBed.createComponent(InsightsAgentsPersonal);
    fixture.detectChanges();
    await fixture.whenStable();
    expect(fixture.componentInstance.loadState()).toBe('error');
  });

  it('requestDeleteAgent opens the confirmation dialog without calling the service', async () => {
    const {component, mocks} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
    });
    component.requestDeleteAgent();
    expect(component.showDeleteConfirmation()).toBe(true);
    expect(mocks.agentService.delete).not.toHaveBeenCalled();
  });

  it('requestDeleteAgent is a no-op when there is no existing agent', async () => {
    const {component} = await createFixture();
    component.requestDeleteAgent();
    expect(component.showDeleteConfirmation()).toBe(false);
  });

  it('cancelDeleteAgent closes the dialog without deleting', async () => {
    const {component, mocks} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
    });
    component.requestDeleteAgent();
    component.cancelDeleteAgent();
    expect(component.showDeleteConfirmation()).toBe(false);
    expect(mocks.agentService.delete).not.toHaveBeenCalled();
  });

  it('confirmDeleteAgent deletes, shows success feedback, and navigates to /insights/agents', async () => {
    const {component, mocks} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
    });
    component.requestDeleteAgent();
    component.confirmDeleteAgent();
    expect(mocks.agentService.delete).toHaveBeenCalledWith('a1');
    expect(component.showDeleteConfirmation()).toBe(false);
    expect(component.submitting()).toBe(false);
    expect(mocks.feedback.update).toHaveBeenCalledWith(
      expect.objectContaining({type: 'success', message: 'Agent deleted.'}),
    );
    expect(mocks.router.navigate).toHaveBeenCalledWith(['/insights/agents']);
  });

  it('confirmDeleteAgent shows error feedback and does not navigate on failure', async () => {
    const {component, mocks} = await createFixture({
      existingAgents: [{id: 'a1', agent_type: mockProfile.type, agent_name: 'existing-agent'}],
      deleteError: true,
    });
    component.requestDeleteAgent();
    component.confirmDeleteAgent();
    expect(mocks.agentService.delete).toHaveBeenCalledWith('a1');
    expect(component.submitting()).toBe(false);
    expect(mocks.feedback.update).toHaveBeenCalledWith(
      expect.objectContaining({type: 'error', message: 'delete failed'}),
    );
    expect(mocks.router.navigate).not.toHaveBeenCalled();
  });
});
