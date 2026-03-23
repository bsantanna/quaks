import {TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';
import {AccountService, UserProfile} from './account.service';
import {environment} from '../../../environments/environment';

describe('AccountService', () => {
  let service: AccountService;
  let httpTesting: HttpTestingController;

  const mockProfile: UserProfile = {
    username: 'jdoe',
    email: 'jdoe@example.com',
    first_name: 'John',
    last_name: 'Doe',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AccountService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should GET profile', () => {
    service.getProfile().subscribe(profile => {
      expect(profile).toEqual(mockProfile);
    });

    const req = httpTesting.expectOne(`${environment.apiBaseUrl}/auth/profile`);
    expect(req.request.method).toBe('GET');
    req.flush(mockProfile);
  });

  it('should PUT profile', () => {
    const updated: UserProfile = {...mockProfile, first_name: 'Jane'};

    service.updateProfile(updated).subscribe(profile => {
      expect(profile).toEqual(updated);
    });

    const req = httpTesting.expectOne(`${environment.apiBaseUrl}/auth/profile`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual(updated);
    req.flush(updated);
  });

  it('should propagate GET errors', () => {
    service.getProfile().subscribe({
      error: err => {
        expect(err.status).toBe(401);
      },
    });

    const req = httpTesting.expectOne(`${environment.apiBaseUrl}/auth/profile`);
    req.flush(null, {status: 401, statusText: 'Unauthorized'});
  });

  it('should propagate PUT errors', () => {
    service.updateProfile(mockProfile).subscribe({
      error: err => {
        expect(err.status).toBe(409);
      },
    });

    const req = httpTesting.expectOne(`${environment.apiBaseUrl}/auth/profile`);
    req.flush(null, {status: 409, statusText: 'Conflict'});
  });
});
