import {Component, HostListener, inject, signal} from '@angular/core';
import {UpperCasePipe} from '@angular/common';
import {AuthService} from '../../shared/services/auth.service';

@Component({
  selector: 'app-auth-dropdown',
  imports: [UpperCasePipe],
  templateUrl: './auth-dropdown.html',
  styleUrl: './auth-dropdown.scss',
})
export class AuthDropdownComponent {

  readonly authService = inject(AuthService);
  readonly showMenu = signal(false);

  toggleMenu(): void {
    this.showMenu.update(v => !v);
  }

  login(): void {
    this.authService.initiateLogin();
  }

  logout(): void {
    this.showMenu.set(false);
    this.authService.logout();
  }

  getInitials(): string {
    const session = this.authService.state();
    if (!session?.username) return '?';
    return session.username.charAt(0).toUpperCase();
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    const target = event.target as HTMLElement;
    if (!target.closest('app-auth-dropdown')) {
      this.showMenu.set(false);
    }
  }
}
