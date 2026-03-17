import {Component, inject, signal} from '@angular/core';
import {FormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {SeoService} from '../shared';
import {WaitlistService} from '../shared/services/waitlist.service';

@Component({
  selector: 'app-page-waitlist',
  imports: [ReactiveFormsModule],
  templateUrl: './page-waitlist.html',
  styleUrl: './page-waitlist.scss',
})
export class PageWaitlist {
  private readonly fb = inject(FormBuilder);
  private readonly waitlistService = inject(WaitlistService);

  readonly state = signal<'form' | 'success' | 'duplicate' | 'error'>('form');
  readonly submitting = signal(false);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    first_name: ['', Validators.required],
    last_name: ['', Validators.required],
    username: ['', [Validators.required, Validators.minLength(3)]],
  });

  constructor() {
    inject(SeoService).update({
      title: 'Join the Waiting List',
      description: 'Sign up to get early access to the Quaks quantitative finance platform.',
      path: '/waitlist',
    });
  }

  submit(): void {
    if (this.form.invalid || this.submitting()) return;
    this.submitting.set(true);
    this.waitlistService.register(this.form.getRawValue()).subscribe({
      next: () => {
        this.submitting.set(false);
        this.state.set('success');
      },
      error: (err) => {
        this.submitting.set(false);
        if (err?.status === 409) {
          this.state.set('duplicate');
        } else {
          this.state.set('error');
        }
      },
    });
  }
}
