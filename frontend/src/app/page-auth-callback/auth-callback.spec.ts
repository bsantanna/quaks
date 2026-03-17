import {ComponentFixture, TestBed} from '@angular/core/testing';
import {AuthCallback} from './auth-callback';
import {AuthService} from '../shared/services/auth.service';
import {ActivatedRoute} from '@angular/router';
import {signal} from '@angular/core';

describe('AuthCallback', () => {
  let component: AuthCallback;
  let fixture: ComponentFixture<AuthCallback>;

  const mockAuthService = {
    state: signal(null),
    isLoggedIn: signal(false),
    handleCallback: jest.fn().mockResolvedValue(undefined),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuthCallback],
      providers: [
        {provide: AuthService, useValue: mockAuthService},
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {queryParams: {}},
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AuthCallback);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show error when missing parameters', () => {
    fixture.detectChanges();
    expect(component.error()).toBe('Missing authorization parameters');
  });
});
