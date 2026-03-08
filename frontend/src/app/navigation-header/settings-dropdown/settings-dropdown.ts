import {Component, inject, signal} from '@angular/core';
import {ThemeService} from '../../shared/services/theme.service';
import {ThemeName} from '../../shared/models/navigation.models';

@Component({
  selector: 'app-settings-dropdown',
  imports: [],
  templateUrl: './settings-dropdown.html',
  styleUrl: './settings-dropdown.scss',
})
export class SettingsDropdownComponent {

  readonly themeService = inject(ThemeService);
  readonly showMenu = signal(false);

  toggleMenu(): void {
    this.showMenu.update(v => !v);
  }

  selectTheme(theme: ThemeName): void {
    this.themeService.update({theme});
    this.showMenu.set(false);
  }
}
