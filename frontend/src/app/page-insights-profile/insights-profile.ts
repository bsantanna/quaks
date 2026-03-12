import {Component, inject, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {HttpClient} from '@angular/common/http';
import {ActivatedRoute} from '@angular/router';

interface AgentProfile {
  name: string;
  role: string;
  avatar: string;
  bio: string[];
  ctaLabel?: string;
  ctaLink?: string;
  ctaIcon?: string;
  referenceNotebook?: string;
}

@Component({
  selector: 'app-insights-profile',
  imports: [],
  templateUrl: './insights-profile.html',
  styleUrl: './insights-profile.scss',
})
export class InsightsProfile {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly httpClient = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);

  readonly profile = signal<AgentProfile | null>(null);

  constructor() {
    if (this.isBrowser) {
      const agentName = this.route.snapshot.paramMap.get('agentName');
      if (agentName) {
        this.httpClient.get<AgentProfile>(`/json/insights-agent_${agentName}.json`)
          .subscribe(data => this.profile.set(data));
      }
    }
  }
}
