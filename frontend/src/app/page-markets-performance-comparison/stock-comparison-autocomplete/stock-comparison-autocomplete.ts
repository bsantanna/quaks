import {Component, computed, ElementRef, inject, input, output, signal, viewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {IndexedKeyTicker, IndexedKeyTickerService} from '../../shared';
import {STOCK_MARKETS} from '../../constants';

@Component({
  selector: 'app-stock-comparison-autocomplete',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './stock-comparison-autocomplete.html',
  styleUrl: './stock-comparison-autocomplete.scss',
})
export class StockComparisonAutocomplete {

  readonly symbols = input.required<string[]>();
  readonly symbolsChange = output<string[]>();

  readonly indexedKeyTickerService = inject(IndexedKeyTickerService);
  readonly searchQuery = signal('');
  readonly isOpen = signal(false);
  readonly highlightedIndex = signal(-1);
  readonly dropdownRef = viewChild<ElementRef>('dropdown');

  filteredStocks = computed(() => {
    const query = this.searchQuery().toLowerCase().trim();
    if (!query || query.length === 0) {
      return [];
    }
    const currentSymbols = this.symbols();
    return this.indexedKeyTickerService.indexedKeyTickers().filter(
      (stock) =>
        (stock.key_ticker.toLowerCase().includes(query) || stock.name.toLowerCase().includes(query))
        && STOCK_MARKETS.filter(market => market === stock.index)
        && !currentSymbols.includes(stock.key_ticker)
    ).slice(0, 50);
  });

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
        this.addSymbol(stocks[current]);
      }
    }
  }

  addSymbol(stock: IndexedKeyTicker): void {
    const current = this.symbols();
    if (!current.includes(stock.key_ticker)) {
      this.symbolsChange.emit([...current, stock.key_ticker]);
    }
    this.searchQuery.set('');
    this.isOpen.set(false);
    this.highlightedIndex.set(-1);
  }

  removeSymbol(symbol: string): void {
    this.symbolsChange.emit(this.symbols().filter(s => s !== symbol));
  }

  onClearSearch(): void {
    this.searchQuery.set('');
    this.isOpen.set(false);
    this.highlightedIndex.set(-1);
  }

  private scrollToHighlighted(index: number): void {
    const dropdown = this.dropdownRef()?.nativeElement;
    if (!dropdown) return;
    const items = dropdown.querySelectorAll('button');
    if (items[index]) {
      items[index].scrollIntoView({block: 'nearest'});
    }
  }

}
