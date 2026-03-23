import {Component, inject, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {FormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {AuthService} from '../shared/services/auth.service';
import {AccountService, UserProfile} from '../shared/services/account.service';
import {FeedbackMessageService, SeoService} from '../shared';

@Component({
  selector: 'app-account-profile',
  imports: [ReactiveFormsModule],
  templateUrl: './account-profile.html',
  styleUrl: './account-profile.scss',
})
export class AccountProfile {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly accountService = inject(AccountService);
  private readonly feedbackMessageService = inject(FeedbackMessageService);
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  readonly state = signal<'loading' | 'form' | 'error'>('loading');
  readonly submitting = signal(false);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    first_name: ['', Validators.required],
    last_name: ['', Validators.required],
    username: ['', [Validators.required, Validators.minLength(3)]],
  });

  constructor() {
    inject(SeoService).update({
      title: 'Account Profile',
      description: 'Manage your Quaks account profile.',
      path: '/account/profile',
    });
    if (this.isBrowser) {
      this.loadProfile();
    }
  }

  private loadProfile(): void {
    this.accountService.getProfile().subscribe({
      next: (profile: UserProfile) => {
        this.form.patchValue(profile);
        this.state.set('form');
      },
      error: () => {
        this.state.set('error');
      },
    });
  }

  submit(): void {
    if (this.form.invalid || this.submitting()) return;
    this.submitting.set(true);
    this.accountService.updateProfile(this.form.getRawValue()).subscribe({
      next: () => {
        this.authService.renewToken().finally(() => {
          this.submitting.set(false);
          this.feedbackMessageService.update({
            message: 'Profile updated successfully.',
            type: 'success',
            timeout: 3000,
          });
        });
      },
      error: (err) => {
        this.submitting.set(false);
        if (err?.status === 409) {
          this.feedbackMessageService.update({
            message: 'A user with this email or username already exists.',
            type: 'error',
            timeout: 3000,
          });
        } else {
          this.feedbackMessageService.update({
            message: 'Failed to update profile. Please try again.',
            type: 'error',
            timeout: 3000,
          });
        }
      },
    });
  }
}
