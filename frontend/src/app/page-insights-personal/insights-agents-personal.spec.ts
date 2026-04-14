import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { InsightsAgentsPersonal } from './insights-agents-personal';

describe('InsightsAgentsPersonal', () => {
  let component: InsightsAgentsPersonal;
  let fixture: ComponentFixture<InsightsAgentsPersonal>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsAgentsPersonal],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([])
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InsightsAgentsPersonal);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
