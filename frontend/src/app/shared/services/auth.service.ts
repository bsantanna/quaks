import {computed, effect, inject, Injectable, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser, DOCUMENT} from '@angular/common';
import {HttpClient} from '@angular/common/http';
import {Router} from '@angular/router';
import {firstValueFrom} from 'rxjs';
import {environment} from '../../../environments/environment';
import {AuthSession, SubscriptionTier} from '../models/auth.models';

@Injectable({
  providedIn: 'root',
})
export class AuthService {

  static readonly STORAGE_KEY = 'AuthSession';

  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly document = inject(DOCUMENT);
  private readonly httpClient = inject(HttpClient);
  private readonly router = inject(Router);

  readonly state = signal<AuthSession | null>(this.loadSession());
  private renewalInProgress: Promise<boolean> | null = null;

  readonly isLoggedIn = computed(() => {
    const session = this.state();
    return session !== null && session.expiresAt > Date.now();
  });

  readonly subscriptionTier = computed<SubscriptionTier>(() => {
    const session = this.state();
    return session?.subscriptionTier ?? 'free';
  });

  constructor() {
    effect(() => {
      const session = this.state();
      if (this.isBrowser) {
        if (session) {
          localStorage.setItem(AuthService.STORAGE_KEY, JSON.stringify(session));
        } else {
          localStorage.removeItem(AuthService.STORAGE_KEY);
        }
      }
    });
  }

  initiateLogin(): void {
    if (!this.isBrowser) return;

    const codeVerifier = this.generateCodeVerifier();
    sessionStorage.setItem('pkce_code_verifier', codeVerifier);

    const state = this.generateRandomString(32);
    sessionStorage.setItem('pkce_state', state);

    this.generateCodeChallenge(codeVerifier).then(codeChallenge => {
      const redirectUri = `${this.document.location.origin}/auth/callback`;
      const params = new URLSearchParams({
        response_type: 'code',
        client_id: environment.keycloakClientId,
        redirect_uri: redirectUri,
        scope: 'openid profile email',
        code_challenge: codeChallenge,
        code_challenge_method: 'S256',
        state: state,
      });

      const authUrl = `${environment.keycloakUrl}/realms/${environment.keycloakRealm}/protocol/openid-connect/auth?${params.toString()}`;
      this.document.location.href = authUrl;
    });
  }

  async handleCallback(code: string, returnedState: string): Promise<void> {
    if (!this.isBrowser) throw new Error('handleCallback requires browser context');

    const savedState = sessionStorage.getItem('pkce_state');
    if (returnedState !== savedState) {
      this.clearPkceStorage();
      throw new Error('Invalid state parameter');
    }

    const codeVerifier = sessionStorage.getItem('pkce_code_verifier');
    if (!codeVerifier) {
      this.clearPkceStorage();
      throw new Error('Missing code verifier');
    }

    const redirectUri = `${this.document.location.origin}/auth/callback`;

    try {
      const response = await firstValueFrom(
        this.httpClient.post<{ access_token: string; refresh_token: string }>(
          `${environment.apiBaseUrl}/auth/exchange`,
          {code, code_verifier: codeVerifier, redirect_uri: redirectUri},
        )
      );

      const session = this.parseTokens(response.access_token, response.refresh_token);
      this.state.set(session);
    } finally {
      this.clearPkceStorage();
    }
  }

  private clearPkceStorage(): void {
    if (!this.isBrowser) return;
    sessionStorage.removeItem('pkce_code_verifier');
    sessionStorage.removeItem('pkce_state');
  }

  async renewToken(): Promise<boolean> {
    if (this.renewalInProgress) return this.renewalInProgress;
    this.renewalInProgress = this.doRenew().finally(() => {
      this.renewalInProgress = null;
    });
    return this.renewalInProgress;
  }

  private async doRenew(): Promise<boolean> {
    const session = this.state();
    if (!session?.refreshToken) return false;

    try {
      const response = await firstValueFrom(
        this.httpClient.post<{ access_token: string; refresh_token: string }>(
          `${environment.apiBaseUrl}/auth/renew`,
          {refresh_token: session.refreshToken},
        )
      );
      const newSession = this.parseTokens(response.access_token, response.refresh_token);
      this.state.set(newSession);
      return true;
    } catch {
      this.logout();
      return false;
    }
  }

  logout(): void {
    this.state.set(null);
    if (this.isBrowser) {
      const logoutUrl = `${environment.keycloakUrl}/realms/${environment.keycloakRealm}/protocol/openid-connect/logout?post_logout_redirect_uri=${encodeURIComponent(this.document.location.origin)}&client_id=${environment.keycloakClientId}`;
      this.document.location.href = logoutUrl;
    }
  }

  getAccessToken(): string | null {
    const session = this.state();
    if (!session || session.expiresAt <= Date.now()) return null;
    return session.accessToken;
  }

  private parseTokens(accessToken: string, refreshToken: string): AuthSession {
    const payload = this.decodeJwtPayload(accessToken);
    const realmAccess = payload?.['realm_access'] as Record<string, unknown> | undefined;
    const roles: string[] = (realmAccess?.['roles'] as string[]) ?? [];
    const subscriptionTier: SubscriptionTier = roles.includes('pro') ? 'pro' : 'free';

    return {
      accessToken,
      refreshToken,
      username: (payload?.['preferred_username'] as string) ?? '',
      email: (payload?.['email'] as string) ?? '',
      firstName: (payload?.['given_name'] as string) ?? '',
      lastName: (payload?.['family_name'] as string) ?? '',
      subscriptionTier,
      expiresAt: ((payload?.['exp'] as number) ?? 0) * 1000,
    };
  }

  private decodeJwtPayload(token: string): Record<string, any> {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return {};
      const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(payload));
    } catch {
      return {};
    }
  }

  private loadSession(): AuthSession | null {
    if (!this.isBrowser) return null;
    const stored = localStorage.getItem(AuthService.STORAGE_KEY);
    if (!stored) return null;
    try {
      const session: AuthSession = JSON.parse(stored);
      if (session.expiresAt <= Date.now()) {
        localStorage.removeItem(AuthService.STORAGE_KEY);
        return null;
      }
      return session;
    } catch {
      return null;
    }
  }

  private generateCodeVerifier(): string {
    const array = new Uint8Array(64);
    crypto.getRandomValues(array);
    return this.base64UrlEncode(array);
  }

  private generateRandomString(length: number): string {
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    return this.base64UrlEncode(array).substring(0, length);
  }

  private async generateCodeChallenge(verifier: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return this.base64UrlEncode(new Uint8Array(digest));
  }

  private base64UrlEncode(buffer: Uint8Array): string {
    let binary = '';
    for (let i = 0; i < buffer.byteLength; i++) {
      binary += String.fromCharCode(buffer[i]);
    }
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
}
