import {Component, inject, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {ActivatedRoute} from '@angular/router';
import {AgentProfile} from '../shared/models/insights.model';
import {InsightsAgentProfileService} from '../shared/services/insights-agent-profile.service';

@Component({
  selector: 'app-insights-profile',
  imports: [],
  templateUrl: './insights-profile.html',
  styleUrl: './insights-profile.scss',
})
export class InsightsProfile {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly agentProfileService = inject(InsightsAgentProfileService);

  readonly profile = signal<AgentProfile | null>(null);

  agentSlug(agent: AgentProfile): string {
    return agent.type.replaceAll('_', '-');
  }

  constructor() {
    if (this.isBrowser) {
      const agentName = this.route.snapshot.paramMap.get('agentName');
      if (agentName) {
        this.agentProfileService.getAgentProfile(agentName)
          .subscribe(data => this.profile.set(data));
      }
    }
  }
}
