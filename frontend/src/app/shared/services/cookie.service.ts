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
    if (storedConsent === null) {
      this.state = signal(CookieService.INITIAL_COOKIE_CONSENT);
    } else {
      this.state = signal(JSON.parse(storedConsent));
    }
  }

  update(cookieConsent: CookieConsent): void {
    this.state.set(cookieConsent);
  }

  resetConsent(): void {
    delete this.document.documentElement.dataset['cookieConsent'];
    this.state.set(CookieService.INITIAL_COOKIE_CONSENT);
  }

  setCookie(name: string, value: string, days: number) {
    if (!this.isBrowser) return;
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = '; expires=' + date.toUTCString();
    let cookie = name + '=' + value + expires + '; path=/; SameSite=Lax';
    if (this.isBrowser && globalThis.isSecureContext) {
      cookie += '; Secure';
    }
    document.cookie = cookie;
  }

  getCookie(name: string): string | null {
    if (!this.isBrowser) return null;
    const nameEQ = name + '=';
    const ca = document.cookie.split(';');
    for (const entry of ca) {
      const c = entry.trimStart();
      if (c.startsWith(nameEQ)) return c.substring(nameEQ.length);
    }
    return null;
  }

}
