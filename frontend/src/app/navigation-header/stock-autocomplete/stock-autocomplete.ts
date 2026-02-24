import {Component, computed, inject, input, output, signal} from '@angular/core';

import {FormsModule} from '@angular/forms';
import {IndexedKeyTicker, IndexedKeyTickerService} from '../../shared';
import {STOCK_MARKETS} from '../../constants';


@Component({
  selector: 'app-stock-autocomplete',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './stock-autocomplete.html',
  styleUrl: './stock-autocomplete.scss',
})
export class StockAutocompleteComponent {

  readonly inputPlaceholder = input('Search stocks (e.g., NVDA, GOOG)');
  readonly indexedKeyTickerService = inject(IndexedKeyTickerService);
  readonly searchQuery = signal('');
  readonly isOpen = signal(false);
  readonly highlightedIndex = signal(-1);

  // Filtered stocks based on search query
  filteredStocks = computed(() => {
    const query = this.searchQuery().toLowerCase().trim();

    if (!query || query.length === 0) {
      return [];
    }

    return this.indexedKeyTickerService.indexedKeyTickers().filter(
      (stock) =>
        (stock.key_ticker.toLowerCase().includes(query) || stock.name.toLowerCase().includes(query))
        && STOCK_MARKETS.filter(market => market === stock.index)
    );

  });

  // Output event for when a stock is selected
  stockSelected = output<IndexedKeyTicker>();

  onSearch(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.searchQuery.set(target.value);
    this.isOpen.set(target.value.length > 0);
    this.highlightedIndex.set(-1);
  }

  onInputFocus(): void {
    if (this.searchQuery().length > 0) {
      this.isOpen.set(true);
    }
  }

  onInputBlur(): void {
    // Delay to allow click on dropdown item to register
    setTimeout(() => {
      this.isOpen.set(false);
      this.highlightedIndex.set(-1);
    }, 200);
  }

  onKeyDown(event: KeyboardEvent): void {
    const stocks = this.filteredStocks();
    if (!this.isOpen() || stocks.length === 0) return;

    const current = this.highlightedIndex();

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      this.highlightedIndex.set(current < stocks.length - 1 ? current + 1 : 0);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      this.highlightedIndex.set(current > 0 ? current - 1 : stocks.length - 1);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      if (current >= 0 && current < stocks.length) {
        this.onSelectStock(stocks[current]);
      }
    }
  }

  onSelectStock(stock: IndexedKeyTicker): void {
    this.searchQuery.set('');
    this.isOpen.set(false);
    this.highlightedIndex.set(-1);
    this.stockSelected.emit(stock);
  }

  onClearSearch(): void {
    this.searchQuery.set('');
    this.isOpen.set(false);
    this.highlightedIndex.set(-1);
  }

}
