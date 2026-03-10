import {effect, inject, Injectable, PLATFORM_ID, signal, WritableSignal} from '@angular/core';
import {isPlatformBrowser, DOCUMENT} from '@angular/common';
import {CookieConsent, SharedStateService} from '../models/navigation.models';

@Injectable({
  providedIn: 'root',
})
export class CookieService implements SharedStateService<CookieConsent> {

  static readonly INITIAL_COOKIE_CONSENT: CookieConsent = {
    consentGiven: false,
    type: 'essential_only',
  };

  static readonly COOKIE_CONSENT_KEY = "CookieConsent"

  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly document = inject(DOCUMENT);
  readonly state!: WritableSignal<CookieConsent>;

  constructor() {
    effect(() => {
      const consent = this.state();
      if (consent.consentGiven) {
        this.setCookie(CookieService.COOKIE_CONSENT_KEY, JSON.stringify(consent), 365);
      }
    });

    const storedConsent = this.getCookie(CookieService.COOKIE_CONSENT_KEY);
    if (storedConsent !== null) {
      this.state = signal(JSON.parse(storedConsent));
    } else {
      this.state = signal(CookieService.INITIAL_COOKIE_CONSENT);
    }
  }

  update(cookieConsent: CookieConsent): void {
    this.state.set(cookieConsent);
  }

  resetConsent(): void {
    this.document.documentElement.removeAttribute('data-cookie-consent');
    this.state.set(CookieService.INITIAL_COOKIE_CONSENT);
  }

  setCookie(name: string, value: string, days: number) {
    if (!this.isBrowser) return;
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = '; expires=' + date.toUTCString();
    let cookie = name + '=' + value + expires + '; path=/; SameSite=Lax';
    if (this.isBrowser && window.isSecureContext) {
      cookie += '; Secure';
    }
    document.cookie = cookie;
  }

  getCookie(name: string): string | null {
    if (!this.isBrowser) return null;
    const nameEQ = name + '=';
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
  }

}
