import {Component, inject, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {ActivatedRoute} from '@angular/router';
import {AgentProfile} from '../shared/models/insights.model';
import {InsightsAgentProfileService} from '../shared/services/insights-agent-profile.service';

@Component({
  selector: 'app-insights-agents-personal',
  imports: [],
  templateUrl: './insights-agents-personal.html',
  styleUrl: './insights-agents-personal.scss',
})
export class InsightsAgentsPersonal {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly agentProfileService = inject(InsightsAgentProfileService);

  readonly agentProfile = signal<AgentProfile | null>(null);

  constructor() {
    if (this.isBrowser) {
      const agentType = this.route.snapshot.paramMap.get('agentType');
      if (agentType) {
        this.agentProfileService.getAgentProfile(agentType)
          .subscribe(data => this.agentProfile.set(data));
      }
    }
  }
}
