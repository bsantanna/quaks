import {Component, computed, ElementRef, inject, input, output, signal, viewChild} from '@angular/core';

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
  readonly dropdownRef = viewChild<ElementRef>('dropdown');

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
    ).slice(0, 50);

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
      const next = current < stocks.length - 1 ? current + 1 : 0;
      this.highlightedIndex.set(next);
      this.scrollToHighlighted(next);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      const prev = current > 0 ? current - 1 : stocks.length - 1;
      this.highlightedIndex.set(prev);
      this.scrollToHighlighted(prev);
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

  private scrollToHighlighted(index: number): void {
    const dropdown = this.dropdownRef()?.nativeElement;
    if (!dropdown) return;
    const items = dropdown.querySelectorAll('button');
    if (items[index]) {
      items[index].scrollIntoView({block: 'nearest'});
    }
  }

  onClearSearch(): void {
    this.searchQuery.set('');
    this.isOpen.set(false);
    this.highlightedIndex.set(-1);
  }

}
