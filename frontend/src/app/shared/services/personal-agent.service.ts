import {inject, Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';
import {environment} from '../../../environments/environment';
import {
  PersonalAgent,
  PersonalAgentCreateRequest,
  PersonalAgentExpanded,
  PersonalAgentSettingUpdateRequest,
  PersonalAgentUpdateRequest,
} from '../models/personal-agent.models';

@Injectable({
  providedIn: 'root',
})
export class PersonalAgentService {

  private readonly httpClient = inject(HttpClient);
  private readonly baseUrl = `${environment.apiBaseUrl}/agents`;

  list(): Observable<PersonalAgent[]> {
    return this.httpClient.get<PersonalAgent[]>(`${this.baseUrl}/list`);
  }

  getById(agentId: string): Observable<PersonalAgentExpanded> {
    return this.httpClient.get<PersonalAgentExpanded>(`${this.baseUrl}/${agentId}`);
  }

  create(payload: PersonalAgentCreateRequest): Observable<PersonalAgent> {
    return this.httpClient.post<PersonalAgent>(`${this.baseUrl}/create`, payload);
  }

  update(payload: PersonalAgentUpdateRequest): Observable<PersonalAgent> {
    return this.httpClient.post<PersonalAgent>(`${this.baseUrl}/update`, payload);
  }

  updateSetting(payload: PersonalAgentSettingUpdateRequest): Observable<PersonalAgentExpanded> {
    return this.httpClient.post<PersonalAgentExpanded>(`${this.baseUrl}/update_setting`, payload);
  }

  resetSettings(agentId: string): Observable<PersonalAgentExpanded> {
    return this.httpClient.post<PersonalAgentExpanded>(`${this.baseUrl}/${agentId}/reset_settings`, {});
  }
}
