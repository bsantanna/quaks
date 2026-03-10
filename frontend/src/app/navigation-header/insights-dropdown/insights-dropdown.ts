import {Component, HostListener, inject, signal} from '@angular/core';
import {Router} from '@angular/router';

@Component({
  selector: 'app-insights-dropdown',
  imports: [],
  templateUrl: './insights-dropdown.html',
  styleUrl: './insights-dropdown.scss',
})
export class InsightsDropdownComponent {
  private readonly router = inject(Router);
  readonly showMenu = signal(false);

  toggleMenu(): void {
    this.showMenu.update(v => !v);
  }

  navigate(path: string): void {
    this.router.navigate([path]);
    this.showMenu.set(false);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    const target = event.target as HTMLElement;
    if (!target.closest('app-insights-dropdown')) {
      this.showMenu.set(false);
    }
  }
}
