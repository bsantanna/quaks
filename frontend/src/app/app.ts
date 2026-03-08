import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import {NavigationHeader} from './navigation-header';
import {NavigationFooter} from './navigation-footer';
import {ThemeService} from './shared/services/theme.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, NavigationHeader, NavigationFooter],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  private readonly themeService = inject(ThemeService);
}
