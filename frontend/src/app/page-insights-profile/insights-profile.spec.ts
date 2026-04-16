import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { InsightsProfile } from './insights-profile';

describe('InsightsProfile', () => {
  let component: InsightsProfile;
  let fixture: ComponentFixture<InsightsProfile>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsProfile],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([])
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InsightsProfile);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('converts agent type underscores to hyphens via agentSlug', () => {
    expect(component.agentSlug({type: 'macro_research'} as any)).toBe('macro-research');
  });
});
