import {TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';
import {PersonalAgentService} from './personal-agent.service';
import {environment} from '../../../environments/environment';

describe('PersonalAgentService', () => {
  let service: PersonalAgentService;
  let http: HttpTestingController;
  const baseUrl = `${environment.apiBaseUrl}/agents`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(PersonalAgentService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('GET /agents/list', () => {
    service.list().subscribe();
    const req = http.expectOne(`${baseUrl}/list`);
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('GET /agents/{id}', () => {
    service.getById('a1').subscribe();
    const req = http.expectOne(`${baseUrl}/a1`);
    expect(req.request.method).toBe('GET');
    req.flush({});
  });

  it('POST /agents/create without language model', () => {
    service.create({agent_name: 'n', agent_type: 'test_echo'}).subscribe();
    const req = http.expectOne(`${baseUrl}/create`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({agent_name: 'n', agent_type: 'test_echo'});
    req.flush({});
  });

  it('POST /agents/update', () => {
    service.update({agent_id: 'a1', agent_name: 'n', agent_summary: 's'}).subscribe();
    const req = http.expectOne(`${baseUrl}/update`);
    expect(req.request.body).toEqual({agent_id: 'a1', agent_name: 'n', agent_summary: 's'});
    req.flush({});
  });

  it('POST /agents/update_setting', () => {
    service.updateSetting({agent_id: 'a1', setting_key: 'k', setting_value: 'v'}).subscribe();
    const req = http.expectOne(`${baseUrl}/update_setting`);
    expect(req.request.body).toEqual({agent_id: 'a1', setting_key: 'k', setting_value: 'v'});
    req.flush({});
  });

  it('POST /agents/{id}/reset_settings', () => {
    service.resetSettings('a1').subscribe();
    const req = http.expectOne(`${baseUrl}/a1/reset_settings`);
    expect(req.request.method).toBe('POST');
    req.flush({});
  });
});
