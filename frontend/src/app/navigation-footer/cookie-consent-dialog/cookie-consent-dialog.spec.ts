import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';

import { CookieConsentDialogComponent } from './cookie-consent-dialog';
import { CookieService } from '../../shared';

describe('CookieConsentDialog', () => {
  let component: CookieConsentDialogComponent;
  let fixture: ComponentFixture<CookieConsentDialogComponent>;
  const mockCookieService = {
    state: signal({consentGiven: false, type: 'essential_only' as const}),
    update: jest.fn(),
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    await TestBed.configureTestingModule({
      imports: [CookieConsentDialogComponent],
      providers: [
        {provide: CookieService, useValue: mockCookieService},
      ],
    })
    .compileComponents();

    fixture = TestBed.createComponent(CookieConsentDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should call update with essential_only consent', () => {
    component.updateConsent('essential_only');
    expect(mockCookieService.update).toHaveBeenCalledWith({consentGiven: true, type: 'essential_only'});
  });

  it('should call update with all consent', () => {
    component.updateConsent('all');
    expect(mockCookieService.update).toHaveBeenCalledWith({consentGiven: true, type: 'all'});
  });
});
