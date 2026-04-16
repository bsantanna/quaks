import { TestBed } from '@angular/core/testing';

import { CookieService } from './cookie.service';

describe('CookieConsent', () => {
  let service: CookieService;

  beforeEach(() => {
    document.cookie = 'CookieConsent=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    delete document.documentElement.dataset['cookieConsent'];
    TestBed.configureTestingModule({});
    service = TestBed.inject(CookieService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('starts with the default consent state', () => {
    expect(service.state()).toEqual({
      consentGiven: false,
      type: 'essential_only',
    });
  });

  it('writes a cookie when consent is given', () => {
    service.update({consentGiven: true, type: 'all'});
    TestBed.flushEffects();

    expect(document.cookie).toContain('CookieConsent=');
    expect(service.getCookie(CookieService.COOKIE_CONSENT_KEY)).toContain('"type":"all"');
  });

  it('can set and read cookies directly', () => {
    service.setCookie('custom', 'value', 1);
    expect(service.getCookie('custom')).toBe('value');
  });

  it('returns null for a cookie that does not exist', () => {
    expect(service.getCookie('NonExistentCookie')).toBeNull();
  });

  it('reads stored consent from cookie on init', () => {
    const consent = {consentGiven: true, type: 'all'};
    document.cookie = `CookieConsent=${JSON.stringify(consent)}; path=/`;

    const freshService = TestBed.inject(CookieService);
    expect(freshService.getCookie(CookieService.COOKIE_CONSENT_KEY)).toContain('"type":"all"');
  });

  it('resets consent state and dataset flags', () => {
    document.documentElement.dataset['cookieConsent'] = 'all';
    service.update({consentGiven: true, type: 'all'});
    service.resetConsent();

    expect(document.documentElement.dataset['cookieConsent']).toBeUndefined();
    expect(service.state()).toEqual(CookieService.INITIAL_COOKIE_CONSENT);
  });
});
