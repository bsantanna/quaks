import {inject, Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';
import {environment} from '../../../environments/environment';

export interface WaitlistRequest {
  email: string;
  first_name: string;
  last_name: string;
  username: string;
}

export interface WaitlistResponse {
  status: string;
}

@Injectable({providedIn: 'root'})
export class WaitlistService {
  private readonly http = inject(HttpClient);
  private readonly url = `${environment.apiBaseUrl}/waitlist`;

  register(payload: WaitlistRequest): Observable<WaitlistResponse> {
    return this.http.post<WaitlistResponse>(this.url, payload);
  }
}
