import {TestBed} from '@angular/core/testing';
import {provideHttpClient, withInterceptors, HttpClient} from '@angular/common/http';
import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';
import {signal} from '@angular/core';
import {provideRouter} from '@angular/router';
import {DOCUMENT} from '@angular/common';

import {authInterceptor} from './auth.interceptor';
import {AuthService} from '../services/auth.service';
import {environment} from '../../../environments/environment';

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpTesting: HttpTestingController;
  let mockAuthService: any;

  beforeEach(() => {
    mockAuthService = {
      state: signal(null),
      isLoggedIn: signal(false),
      getAccessToken: jest.fn().mockReturnValue(null),
      renewToken: jest.fn().mockResolvedValue(false),
    };

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        provideRouter([]),
        {provide: AuthService, useValue: mockAuthService},
        {provide: DOCUMENT, useValue: document},
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should pass through requests without token when not authenticated', () => {
    httpClient.get('/api/test').subscribe();

    const req = httpTesting.expectOne('/api/test');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });

  it('should add Authorization header when token is available', () => {
    mockAuthService.getAccessToken.mockReturnValue('valid-token');

    httpClient.get('/api/test').subscribe();

    const req = httpTesting.expectOne('/api/test');
    expect(req.request.headers.get('Authorization')).toBe('Bearer valid-token');
    req.flush({});
  });

  it('should skip interceptor for keycloak requests', () => {
    mockAuthService.getAccessToken.mockReturnValue('token');

    httpClient.get(`${environment.keycloakUrl}/some/path`).subscribe();

    const req = httpTesting.expectOne(`${environment.keycloakUrl}/some/path`);
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });

  it('should skip interceptor for auth exchange endpoint', () => {
    mockAuthService.getAccessToken.mockReturnValue('token');

    httpClient.post('/api/auth/exchange', {}).subscribe();

    const req = httpTesting.expectOne('/api/auth/exchange');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });

  it('should skip interceptor for auth renew endpoint', () => {
    mockAuthService.getAccessToken.mockReturnValue('token');

    httpClient.post('/api/auth/renew', {}).subscribe();

    const req = httpTesting.expectOne('/api/auth/renew');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });

  it('should propagate 401 when no session exists', (done) => {
    mockAuthService.getAccessToken.mockReturnValue('expired-token');
    // No session — state is null

    httpClient.get('/api/test').subscribe({
      error: (err) => {
        expect(err.status).toBe(401);
        expect(mockAuthService.renewToken).not.toHaveBeenCalled();
        done();
      },
    });

    const req = httpTesting.expectOne('/api/test');
    req.flush('Unauthorized', {status: 401, statusText: 'Unauthorized'});
  });

  it('should attempt token renewal on 401 when session exists', async () => {
    mockAuthService.getAccessToken.mockReturnValue('expired-token');
    mockAuthService.state.set({
      accessToken: 'expired', refreshToken: 'rt', username: 'u',
      email: '', firstName: '', lastName: '', subscriptionTier: 'free',
      expiresAt: Date.now() + 3600000,
    });
    mockAuthService.renewToken.mockResolvedValue(true);
    // After renewal, getAccessToken returns new token
    mockAuthService.getAccessToken.mockReturnValue('new-token');

    const result$ = httpClient.get('/api/data');
    const promise = new Promise<void>((resolve) => {
      result$.subscribe({ next: () => resolve(), error: () => resolve() });
    });

    const req1 = httpTesting.expectOne('/api/data');
    req1.flush('Unauthorized', {status: 401, statusText: 'Unauthorized'});

    // Wait for async renewal
    await new Promise(r => setTimeout(r, 10));

    const retryReqs = httpTesting.match('/api/data');
    if (retryReqs.length > 0) {
      retryReqs[0].flush({ok: true});
    }

    await promise;
    expect(mockAuthService.renewToken).toHaveBeenCalled();
  });

  it('should propagate 401 when renewal fails', (done) => {
    mockAuthService.getAccessToken.mockReturnValue('expired-token');
    mockAuthService.state.set({
      accessToken: 'expired', refreshToken: 'rt', username: 'u',
      email: '', firstName: '', lastName: '', subscriptionTier: 'free',
      expiresAt: Date.now() + 3600000,
    });
    mockAuthService.renewToken.mockResolvedValue(false);

    httpClient.get('/api/data').subscribe({
      error: (err) => {
        expect(err.status).toBe(401);
        done();
      },
    });

    const req = httpTesting.expectOne('/api/data');
    req.flush('Unauthorized', {status: 401, statusText: 'Unauthorized'});
  });

  it('should propagate 401 when renewed token is null', (done) => {
    mockAuthService.getAccessToken
      .mockReturnValueOnce('expired-token')
      .mockReturnValueOnce(null);
    mockAuthService.state.set({
      accessToken: 'expired', refreshToken: 'rt', username: 'u',
      email: '', firstName: '', lastName: '', subscriptionTier: 'free',
      expiresAt: Date.now() + 3600000,
    });
    mockAuthService.renewToken.mockResolvedValue(true);

    httpClient.get('/api/data').subscribe({
      error: (err) => {
        expect(err.status).toBe(401);
        done();
      },
    });

    const req = httpTesting.expectOne('/api/data');
    req.flush('Unauthorized', {status: 401, statusText: 'Unauthorized'});
  });

  it('should propagate non-401 errors without renewal', (done) => {
    mockAuthService.getAccessToken.mockReturnValue('token');

    httpClient.get('/api/test').subscribe({
      error: (err) => {
        expect(err.status).toBe(500);
        done();
      },
    });

    const req = httpTesting.expectOne('/api/test');
    req.flush('Error', {status: 500, statusText: 'Server Error'});
  });
});
