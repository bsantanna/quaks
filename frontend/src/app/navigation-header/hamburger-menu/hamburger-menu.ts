import {Component, inject, input, output, signal} from '@angular/core';
import {Router} from '@angular/router';
import {ThemeService} from '../../shared/services/theme.service';
import {ThemeName} from '../../shared/models/navigation.models';
import {StockAutocompleteComponent} from '../stock-autocomplete/stock-autocomplete';
import {NewsAutocompleteComponent} from '../news-autocomplete/news-autocomplete';
import {IndexedKeyTicker} from '../../shared';
import {STOCK_MARKETS} from '../../constants';

@Component({
  selector: 'app-hamburger-menu',
  imports: [StockAutocompleteComponent, NewsAutocompleteComponent],
  templateUrl: './hamburger-menu.html',
  styleUrl: './hamburger-menu.scss',
})
export class HamburgerMenuComponent {
  private readonly router = inject(Router);
  readonly themeService = inject(ThemeService);
  readonly path = input.required<string>();
  readonly menuOpen = signal(false);
  readonly stockSelected = output<IndexedKeyTicker>();

  toggle(): void {
    this.menuOpen.update(v => !v);
  }

  close(): void {
    this.menuOpen.set(false);
  }

  navigate(path: string): void {
    this.router.navigate([path]);
    this.close();
  }

  selectTheme(theme: ThemeName): void {
    this.themeService.update({theme});
  }

  onKeyTickerSelected(indexedKeyTicker: IndexedKeyTicker): void {
    if (STOCK_MARKETS.filter(market => market === indexedKeyTicker.index)) {
      this.stockSelected.emit(indexedKeyTicker);
      this.close();
    }
  }
}
