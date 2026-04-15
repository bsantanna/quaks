import {Component, inject, input} from '@angular/core';
import {AuthService} from '../../services/auth.service';

@Component({
  selector: 'app-login-required-message',
  imports: [],
  templateUrl: './login-required-message.html',
  styleUrl: './login-required-message.scss',
})
export class LoginRequiredMessage {
  private readonly authService = inject(AuthService);

  readonly notice = input.required<string>();

  login(): void {
    this.authService.initiateLogin();
  }
}
