import {Component, inject, input, output, signal} from '@angular/core';
import {TitleCasePipe, UpperCasePipe} from '@angular/common';
import {Router} from '@angular/router';
import {ThemeService} from '../../shared/services/theme.service';
import {DateFormatService} from '../../shared/services/date-format.service';
import {ThemeName, DateFormatName} from '../../shared/models/navigation.models';
import {AuthService} from '../../shared/services/auth.service';
import {StockAutocompleteComponent} from '../stock-autocomplete/stock-autocomplete';
import {NewsAutocompleteComponent} from '../news-autocomplete/news-autocomplete';
import {IndexedKeyTicker} from '../../shared';
import {STOCK_MARKETS} from '../../constants';

@Component({
  selector: 'app-hamburger-menu',
  imports: [StockAutocompleteComponent, NewsAutocompleteComponent, TitleCasePipe, UpperCasePipe],
  templateUrl: './hamburger-menu.html',
  styleUrl: './hamburger-menu.scss',
})
export class HamburgerMenuComponent {
  private readonly router = inject(Router);
  readonly themeService = inject(ThemeService);
  readonly dateFormatService = inject(DateFormatService);
  readonly authService = inject(AuthService);
  readonly path = input.required<string>();
  readonly menuOpen = signal(false);
  readonly themeOpen = signal(false);
  readonly stockSelected = output<IndexedKeyTicker>();

  toggle(): void {
    this.menuOpen.update(v => !v);
  }

  close(): void {
    this.menuOpen.set(false);
    this.themeOpen.set(false);
  }

  navigate(path: string): void {
    this.router.navigate([path]);
    this.close();
  }

  toggleThemeDropdown(): void {
    this.themeOpen.update(v => !v);
  }

  selectTheme(theme: ThemeName): void {
    this.themeService.update({theme});
    this.themeOpen.set(false);
  }

  selectDateFormat(dateFormat: DateFormatName): void {
    this.dateFormatService.update({dateFormat});
  }

  login(): void {
    this.close();
    this.authService.initiateLogin();
  }

  logout(): void {
    this.close();
    this.authService.logout();
  }

  onKeyTickerSelected(indexedKeyTicker: IndexedKeyTicker): void {
    if (STOCK_MARKETS.includes(indexedKeyTicker.index)) {
      this.stockSelected.emit(indexedKeyTicker);
      this.close();
    }
  }
}
