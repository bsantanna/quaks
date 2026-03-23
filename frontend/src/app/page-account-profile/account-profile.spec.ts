import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {of, throwError} from 'rxjs';
import {AccountProfile} from './account-profile';
import {AccountService} from '../shared/services/account.service';
import {AuthService} from '../shared/services/auth.service';
import {FeedbackMessageService} from '../shared';

describe('AccountProfile', () => {
  let component: AccountProfile;
  let fixture: ComponentFixture<AccountProfile>;
  let accountService: jest.Mocked<Partial<AccountService>>;
  let authService: jest.Mocked<Partial<AuthService>>;
  let feedbackService: jest.Mocked<Partial<FeedbackMessageService>>;

  const mockProfile = {
    username: 'testuser',
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
  };

  beforeEach(async () => {
    accountService = {
      getProfile: jest.fn().mockReturnValue(of(mockProfile)),
      updateProfile: jest.fn().mockReturnValue(of(mockProfile)),
    };
    authService = {
      isLoggedIn: jest.fn().mockReturnValue(true) as any,
      renewToken: jest.fn().mockResolvedValue(true),
      state: jest.fn().mockReturnValue(null) as any,
      subscriptionTier: jest.fn().mockReturnValue('free') as any,
    };
    feedbackService = {
      update: jest.fn(),
      state: jest.fn().mockReturnValue({message: '', type: 'info', timeout: 0}) as any,
    };

    await TestBed.configureTestingModule({
      imports: [AccountProfile],
      providers: [
        provideRouter([]),
        {provide: AccountService, useValue: accountService},
        {provide: AuthService, useValue: authService},
        {provide: FeedbackMessageService, useValue: feedbackService},
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AccountProfile);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load profile and populate form', () => {
    expect(accountService.getProfile).toHaveBeenCalled();
    expect(component.state()).toBe('form');
    expect(component.form.getRawValue()).toEqual(mockProfile);
  });

  it('should set error state when profile load fails', async () => {
    accountService.getProfile!.mockReturnValue(throwError(() => new Error('fail')));
    const fix = TestBed.createComponent(AccountProfile);
    await fix.whenStable();
    expect(fix.componentInstance.state()).toBe('error');
  });

  it('should not submit when form is invalid', () => {
    component.form.reset();
    component.submit();
    expect(accountService.updateProfile).not.toHaveBeenCalled();
  });

  it('should submit and show success feedback', async () => {
    component.submit();
    expect(accountService.updateProfile).toHaveBeenCalledWith(mockProfile);
    await fixture.whenStable();
    expect(authService.renewToken).toHaveBeenCalled();
    expect(feedbackService.update).toHaveBeenCalledWith(
      expect.objectContaining({type: 'success'})
    );
  });

  it('should show conflict error on 409', () => {
    accountService.updateProfile!.mockReturnValue(throwError(() => ({status: 409})));
    component.submit();
    expect(feedbackService.update).toHaveBeenCalledWith(
      expect.objectContaining({type: 'error', message: expect.stringContaining('already exists')})
    );
  });

  it('should show generic error on failure', () => {
    accountService.updateProfile!.mockReturnValue(throwError(() => ({status: 500})));
    component.submit();
    expect(feedbackService.update).toHaveBeenCalledWith(
      expect.objectContaining({type: 'error', message: expect.stringContaining('Failed')})
    );
  });
});
