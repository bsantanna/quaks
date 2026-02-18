import {Component, inject, input} from '@angular/core';
import {Router} from '@angular/router';

@Component({
  selector: 'app-nav-button',
  imports: [],
  templateUrl: './nav-button.html',
  styleUrl: './nav-button.scss',
})
export class NavButtonComponent {

  private readonly router = inject(Router);
  readonly buttonLabel = input.required<string>();
  readonly navigationPath = input.required<string>();

  navigate(): void {
    this.router.navigate([this.navigationPath()]);
  }

}
