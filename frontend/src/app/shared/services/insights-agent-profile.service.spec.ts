import {TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';

import {InsightsAgentProfileService} from './insights-agent-profile.service';

describe('InsightsAgentProfileService', () => {
  let service: InsightsAgentProfileService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(InsightsAgentProfileService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch a single agent profile', () => {
    const mockProfile = {type: 'news_analyst', name: 'NA', role: 'Reporter', avatar: '/a.svg', bio: ['Bio']};

    service.getAgentProfile('news-analyst').subscribe(result => {
      expect(result).toEqual(mockProfile);
    });

    const req = httpTesting.expectOne('/json/insights-agent_news-analyst.json');
    expect(req.request.method).toBe('GET');
    req.flush(mockProfile);
  });

  it('should fetch all agent profiles via slugs list', () => {
    const slugs = ['news-analyst', 'financial-analyst'];
    const profiles = [
      {type: 'news_analyst', name: 'NA', role: 'Reporter', avatar: '/a.svg', bio: []},
      {type: 'financial_analyst', name: 'FA', role: 'Analyst', avatar: '/b.svg', bio: []},
    ];

    service.getAllAgentProfiles().subscribe(result => {
      expect(result).toEqual(profiles);
    });

    const slugReq = httpTesting.expectOne('/json/insights-agents.json');
    slugReq.flush(slugs);

    const req1 = httpTesting.expectOne('/json/insights-agent_news-analyst.json');
    req1.flush(profiles[0]);

    const req2 = httpTesting.expectOne('/json/insights-agent_financial-analyst.json');
    req2.flush(profiles[1]);
  });
});
