import {Component, inject, signal} from '@angular/core';
import {TitleCasePipe} from '@angular/common';
import {ThemeService} from '../../shared/services/theme.service';
import {DateFormatService} from '../../shared/services/date-format.service';
import {ThemeName, DateFormatName} from '../../shared/models/navigation.models';

@Component({
  selector: 'app-settings-dropdown',
  imports: [TitleCasePipe],
  templateUrl: './settings-dropdown.html',
  styleUrl: './settings-dropdown.scss',
})
export class SettingsDropdownComponent {

  readonly themeService = inject(ThemeService);
  readonly dateFormatService = inject(DateFormatService);
  readonly showMenu = signal(false);
  readonly themeOpen = signal(false);

  toggleMenu(): void {
    this.showMenu.update(v => !v);
    this.themeOpen.set(false);
  }

  toggleThemeDropdown(): void {
    this.themeOpen.update(v => !v);
  }

  selectTheme(theme: ThemeName): void {
    this.themeService.update({theme});
    this.themeOpen.set(false);
    this.showMenu.set(false);
  }

  selectDateFormat(dateFormat: DateFormatName): void {
    this.dateFormatService.update({dateFormat});
    this.showMenu.set(false);
  }
}
