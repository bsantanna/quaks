import {inject, Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';
import {environment} from '../../../environments/environment';

export interface UserProfile {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

@Injectable({
  providedIn: 'root',
})
export class AccountService {

  private readonly httpClient = inject(HttpClient);
  private readonly profileUrl = `${environment.apiBaseUrl}/auth/profile`;

  getProfile(): Observable<UserProfile> {
    return this.httpClient.get<UserProfile>(this.profileUrl);
  }

  updateProfile(payload: UserProfile): Observable<UserProfile> {
    return this.httpClient.put<UserProfile>(this.profileUrl, payload);
  }
}
