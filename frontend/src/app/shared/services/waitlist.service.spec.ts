import {TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';

import {WaitlistService, WaitlistRequest, WaitlistResponse} from './waitlist.service';
import {environment} from '../../../environments/environment';

describe('WaitlistService', () => {
  let service: WaitlistService;
  let httpTesting: HttpTestingController;

  const url = `${environment.apiBaseUrl}/waitlist`;

  const payload: WaitlistRequest = {
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
    username: 'testuser',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(WaitlistService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should POST to the waitlist endpoint with the payload', () => {
    const mockResponse: WaitlistResponse = {status: 'registered'};

    service.register(payload).subscribe((result) => {
      expect(result).toEqual(mockResponse);
    });

    const req = httpTesting.expectOne(url);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(mockResponse);
  });

  it('should return the response status from the server', () => {
    service.register(payload).subscribe((result) => {
      expect(result.status).toBe('registered');
    });

    const req = httpTesting.expectOne(url);
    req.flush({status: 'registered'});
  });

  it('should propagate HTTP errors to the caller', () => {
    let caughtError: any;

    service.register(payload).subscribe({
      next: () => fail('expected an error'),
      error: (err) => (caughtError = err),
    });

    const req = httpTesting.expectOne(url);
    req.flush({detail: 'Email already registered'}, {status: 409, statusText: 'Conflict'});

    expect(caughtError).toBeTruthy();
    expect(caughtError.status).toBe(409);
  });
});
