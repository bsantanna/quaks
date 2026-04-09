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
    jest.clearAllMocks();
    mockAuthService.state.set(null);
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

  it('toggles and closes the menu', () => {
    component.toggleMenu();
    expect(component.showMenu()).toBe(true);

    component.onDocumentClick({target: document.createElement('div')} as Event);
    expect(component.showMenu()).toBe(false);
  });

  it('logs out and closes the menu', () => {
    component.showMenu.set(true);
    component.logout();

    expect(component.showMenu()).toBe(false);
    expect(mockAuthService.logout).toHaveBeenCalled();
  });

  it('returns the uppercase user initial', () => {
    mockAuthService.state.set({username: 'bruno'});
    expect(component.getInitials()).toBe('B');
  });
});
