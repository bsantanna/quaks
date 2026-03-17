import {Component, inject, OnInit, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {ActivatedRoute, Router} from '@angular/router';
import {AuthService} from '../shared/services/auth.service';

@Component({
  selector: 'app-auth-callback',
  imports: [],
  template: `
    <div class="callback-container">
      @if (error()) {
        <p class="callback-error">{{ error() }}</p>
        <button class="callback-btn" (click)="goHome()">Return to Home</button>
      } @else {
        <p class="callback-message">Signing you in...</p>
      }
    </div>
  `,
  styles: [`
    .callback-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 50vh;
      gap: 16px;
    }
    .callback-message {
      color: var(--text-secondary);
      font-family: var(--font-body);
      font-size: 16px;
    }
    .callback-error {
      color: var(--status-negative);
      font-family: var(--font-body);
      font-size: 14px;
    }
    .callback-btn {
      padding: 8px 16px;
      background: var(--accent-primary);
      color: var(--surface-base);
      border: none;
      border-radius: var(--radius);
      font-family: var(--font-body);
      cursor: pointer;
    }
  `],
})
export class AuthCallback implements OnInit {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);

  readonly error = signal('');

  ngOnInit(): void {
    if (!this.isBrowser) return;

    const params = this.route.snapshot.queryParams;
    const oauthError = params['error'];
    if (oauthError) {
      const desc = params['error_description'] || 'Login was cancelled or denied';
      this.error.set(desc);
      return;
    }

    const code = params['code'];
    const state = params['state'];

    if (!code || !state) {
      this.error.set('Missing authorization parameters');
      return;
    }

    this.authService.handleCallback(code, state).then(
      () => this.router.navigate(['/']),
      (err) => this.error.set(err?.message ?? 'Authentication failed'),
    );
  }

  goHome(): void {
    this.router.navigate(['/']);
  }
}
