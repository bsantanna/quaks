import {TestBed} from '@angular/core/testing';
import {provideRouter, Router} from '@angular/router';
import {provideHttpClient} from '@angular/common/http';
import {Component} from '@angular/core';
import {authGuard} from './auth.guard';
import {AuthService} from '../services/auth.service';

@Component({template: ''})
class DummyComponent {}

describe('authGuard', () => {
  let authService: jest.Mocked<Partial<AuthService>>;
  let router: Router;

  beforeEach(() => {
    localStorage.clear();
    authService = {
      isLoggedIn: jest.fn().mockReturnValue(false) as any,
      initiateLogin: jest.fn(),
      state: jest.fn().mockReturnValue(null) as any,
      subscriptionTier: jest.fn().mockReturnValue('free') as any,
      getAccessToken: jest.fn().mockReturnValue(null),
    };

    TestBed.configureTestingModule({
      providers: [
        provideRouter([
          {path: 'protected', component: DummyComponent, canActivate: [authGuard]},
          {path: '', component: DummyComponent},
        ]),
        provideHttpClient(),
        {provide: AuthService, useValue: authService},
      ],
    });

    router = TestBed.inject(Router);
  });

  it('should allow access when logged in', async () => {
    (authService.isLoggedIn as jest.Mock).mockReturnValue(true);
    const result = await router.navigateByUrl('/protected');
    expect(result).toBe(true);
    expect(authService.initiateLogin).not.toHaveBeenCalled();
  });

  it('should block access and initiate login when not logged in', async () => {
    (authService.isLoggedIn as jest.Mock).mockReturnValue(false);
    const result = await router.navigateByUrl('/protected');
    expect(result).toBe(false);
    expect(authService.initiateLogin).toHaveBeenCalled();
  });
});
