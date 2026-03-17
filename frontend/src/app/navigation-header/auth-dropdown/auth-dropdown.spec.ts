import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {AuthDropdownComponent} from './auth-dropdown';
import {AuthService} from '../../shared/services/auth.service';
import {signal} from '@angular/core';

describe('AuthDropdownComponent', () => {
  let component: AuthDropdownComponent;
  let fixture: ComponentFixture<AuthDropdownComponent>;

  const mockAuthService = {
    state: signal(null),
    isLoggedIn: signal(false),
    subscriptionTier: signal('free' as const),
    initiateLogin: jest.fn(),
    logout: jest.fn(),
    getAccessToken: jest.fn().mockReturnValue(null),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuthDropdownComponent],
      providers: [
        provideRouter([]),
        {provide: AuthService, useValue: mockAuthService},
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AuthDropdownComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show account button when not logged in', () => {
    const el: HTMLElement = fixture.nativeElement;
    const accountBtn = el.querySelector('.auth-btn');
    expect(accountBtn).toBeTruthy();
  });

  it('should call initiateLogin on login click', () => {
    component.login();
    expect(mockAuthService.initiateLogin).toHaveBeenCalled();
  });

  it('should return ? for initials when no session', () => {
    expect(component.getInitials()).toBe('?');
  });
});
