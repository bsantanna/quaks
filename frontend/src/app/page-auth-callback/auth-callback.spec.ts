import {ComponentFixture, TestBed} from '@angular/core/testing';
import {AuthCallback} from './auth-callback';
import {AuthService} from '../shared/services/auth.service';
import {ActivatedRoute, Router} from '@angular/router';
import {signal} from '@angular/core';

describe('AuthCallback', () => {
  let component: AuthCallback;
  let fixture: ComponentFixture<AuthCallback>;
  let mockAuthService: any;
  let mockRouter: any;

  function createComponent(queryParams: Record<string, string>) {
    mockAuthService = {
      state: signal(null),
      isLoggedIn: signal(false),
      handleCallback: jest.fn().mockResolvedValue(undefined),
    };
    mockRouter = {navigate: jest.fn().mockResolvedValue(true)};

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [AuthCallback],
      providers: [
        {provide: AuthService, useValue: mockAuthService},
        {provide: Router, useValue: mockRouter},
        {provide: ActivatedRoute, useValue: {snapshot: {queryParams}}},
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AuthCallback);
    component = fixture.componentInstance;
  }

  it('should create', () => {
    createComponent({});
    expect(component).toBeTruthy();
  });

  it('should show error when missing parameters', () => {
    createComponent({});
    fixture.detectChanges();
    expect(component.error()).toBe('Missing authorization parameters');
  });

  it('should show oauth error description', () => {
    createComponent({error: 'access_denied', error_description: 'User denied'});
    fixture.detectChanges();
    expect(component.error()).toBe('User denied');
  });

  it('should show default error description when missing', () => {
    createComponent({error: 'access_denied'});
    fixture.detectChanges();
    expect(component.error()).toBe('Login was cancelled or denied');
  });

  it('should call handleCallback with code and state', async () => {
    createComponent({code: 'auth-code', state: 'state-123'});
    fixture.detectChanges();

    expect(mockAuthService.handleCallback).toHaveBeenCalledWith('auth-code', 'state-123');
    await fixture.whenStable();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/']);
  });

  it('should show error on handleCallback failure', async () => {
    createComponent({code: 'bad-code', state: 'state-123'});
    mockAuthService.handleCallback.mockRejectedValue(new Error('Auth failed'));
    fixture.detectChanges();

    await fixture.whenStable();
    expect(component.error()).toBe('Auth failed');
  });

  it('should navigate home on goHome', () => {
    createComponent({});
    fixture.detectChanges();
    component.goHome();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/']);
  });
});
