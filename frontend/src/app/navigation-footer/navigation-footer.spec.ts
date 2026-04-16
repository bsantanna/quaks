import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';

import { NavigationFooter } from './navigation-footer';
import { CookieService } from '../shared';

describe('NavigationFooter', () => {
  let component: NavigationFooter;
  let fixture: ComponentFixture<NavigationFooter>;
  const mockCookieService = {
    resetConsent: jest.fn(),
    update: jest.fn(),
    state: signal({consentGiven: false, type: 'essential_only' as const}),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavigationFooter],
      providers: [
        {provide: CookieService, useValue: mockCookieService},
      ],
    })
    .compileComponents();

    fixture = TestBed.createComponent(NavigationFooter);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should call resetConsent when manageCookies is invoked', () => {
    component.manageCookies();
    expect(mockCookieService.resetConsent).toHaveBeenCalled();
  });
});
