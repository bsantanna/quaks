import {Component, inject, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {AgentProfile} from '../shared/models/insights.model';
import {InsightsAgentProfileService} from '../shared/services/insights-agent-profile.service';

@Component({
  selector: 'app-insights-agents',
  imports: [],
  templateUrl: './insights-agents.html',
  styleUrl: './insights-agents.scss',
})
export class InsightsAgents {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly agentProfileService = inject(InsightsAgentProfileService);

  readonly agents = signal<AgentProfile[]>([]);

  constructor() {
    if (this.isBrowser) {
      this.agentProfileService.getAllAgentProfiles()
        .subscribe(data => this.agents.set(data));
    }
  }

  agentSlug(agent: AgentProfile): string {
    return agent.type.replaceAll('_', '-');
  }
}
