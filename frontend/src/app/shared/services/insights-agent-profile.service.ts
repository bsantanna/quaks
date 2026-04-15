import {inject, Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {AgentProfile} from '../models/insights.model';
import {forkJoin, Observable, switchMap} from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class InsightsAgentProfileService {

  private readonly httpClient = inject(HttpClient);

  getAgentProfile(slug: string): Observable<AgentProfile> {
    return this.httpClient.get<AgentProfile>(`/json/insights-agent_${slug}.json`);
  }

  getAllAgentProfiles(): Observable<AgentProfile[]> {
    return this.httpClient.get<string[]>('/json/insights-agents.json').pipe(
      switchMap(slugs => forkJoin(slugs.map(slug => this.getAgentProfile(slug))))
    );
  }
}
