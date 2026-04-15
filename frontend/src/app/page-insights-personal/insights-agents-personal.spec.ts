import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { AuthService } from '../shared/services/auth.service';

import { InsightsAgentsPersonal } from './insights-agents-personal';

describe('InsightsAgentsPersonal', () => {
  let component: InsightsAgentsPersonal;
  let fixture: ComponentFixture<InsightsAgentsPersonal>;
  const mockAuthService = {
    isLoggedIn: signal(false),
    initiateLogin: jest.fn(),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsAgentsPersonal],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: AuthService, useValue: mockAuthService }
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
