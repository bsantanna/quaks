import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting} from '@angular/common/http/testing';

import {StockAutocompleteComponent} from './stock-autocomplete';
import {IndexedKeyTicker, IndexedKeyTickerService} from '../../shared';

describe('StockAutocompleteComponent', () => {
  let component: StockAutocompleteComponent;
  let fixture: ComponentFixture<StockAutocompleteComponent>;

  const mockTickers: IndexedKeyTicker[] = [
    {key_ticker: 'AAPL', index: 'nasdaq_100', name: 'Apple Inc'},
    {key_ticker: 'GOOG', index: 'nasdaq_100', name: 'Alphabet Inc'},
    {key_ticker: 'MSFT', index: 'nasdaq_100', name: 'Microsoft Corporation'},
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockAutocompleteComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(StockAutocompleteComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with empty search query and closed dropdown', () => {
    expect(component.searchQuery()).toBe('');
    expect(component.isOpen()).toBe(false);
    expect(component.highlightedIndex()).toBe(-1);
  });

  it('should return empty filteredStocks when search query is empty', () => {
    expect(component.filteredStocks()).toEqual([]);
  });

  describe('onSearch', () => {
    it('should update search query and open dropdown', () => {
      const event = {target: {value: 'AAPL'}} as unknown as Event;
      component.onSearch(event);

      expect(component.searchQuery()).toBe('AAPL');
      expect(component.isOpen()).toBe(true);
      expect(component.highlightedIndex()).toBe(-1);
    });

    it('should close dropdown when input is empty', () => {
      const event = {target: {value: ''}} as unknown as Event;
      component.onSearch(event);

      expect(component.searchQuery()).toBe('');
      expect(component.isOpen()).toBe(false);
    });
  });

  describe('onInputFocus', () => {
    it('should open dropdown when search query is not empty', () => {
      component.searchQuery.set('test');
      component.onInputFocus();
      expect(component.isOpen()).toBe(true);
    });

    it('should not open dropdown when search query is empty', () => {
      component.searchQuery.set('');
      component.onInputFocus();
      expect(component.isOpen()).toBe(false);
    });
  });

  describe('onInputBlur', () => {
    it('should close dropdown after delay', (done) => {
      component.isOpen.set(true);
      component.highlightedIndex.set(2);
      component.onInputBlur();

      setTimeout(() => {
        expect(component.isOpen()).toBe(false);
        expect(component.highlightedIndex()).toBe(-1);
        done();
      }, 250);
    });
  });

  describe('onKeyDown', () => {
    beforeEach(() => {
      // Mock the service to return tickers for filtering
      const service = TestBed.inject(IndexedKeyTickerService);
      (service as any).indexedKeyTickers = () => mockTickers;
      component.searchQuery.set('a');
      component.isOpen.set(true);
    });

    it('should not act when dropdown is closed', () => {
      component.isOpen.set(false);
      const event = new KeyboardEvent('keydown', {key: 'ArrowDown'});
      jest.spyOn(event, 'preventDefault');
      component.onKeyDown(event);
      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should move highlight down on ArrowDown', () => {
      const event = new KeyboardEvent('keydown', {key: 'ArrowDown'});
      jest.spyOn(event, 'preventDefault');
      component.onKeyDown(event);
      expect(event.preventDefault).toHaveBeenCalled();
      expect(component.highlightedIndex()).toBe(0);
    });

    it('should wrap around on ArrowDown at end', () => {
      const stocks = component.filteredStocks();
      component.highlightedIndex.set(stocks.length - 1);
      const event = new KeyboardEvent('keydown', {key: 'ArrowDown'});
      component.onKeyDown(event);
      expect(component.highlightedIndex()).toBe(0);
    });

    it('should move highlight up on ArrowUp', () => {
      component.highlightedIndex.set(1);
      const event = new KeyboardEvent('keydown', {key: 'ArrowUp'});
      jest.spyOn(event, 'preventDefault');
      component.onKeyDown(event);
      expect(event.preventDefault).toHaveBeenCalled();
      expect(component.highlightedIndex()).toBe(0);
    });

    it('should wrap around on ArrowUp at beginning', () => {
      component.highlightedIndex.set(0);
      const event = new KeyboardEvent('keydown', {key: 'ArrowUp'});
      component.onKeyDown(event);
      const stocks = component.filteredStocks();
      expect(component.highlightedIndex()).toBe(stocks.length - 1);
    });

    it('should select stock on Enter when highlighted', () => {
      const emitSpy = jest.spyOn(component.stockSelected, 'emit');
      const stocks = component.filteredStocks();
      component.highlightedIndex.set(0);
      const event = new KeyboardEvent('keydown', {key: 'Enter'});
      jest.spyOn(event, 'preventDefault');
      component.onKeyDown(event);
      expect(event.preventDefault).toHaveBeenCalled();
      expect(emitSpy).toHaveBeenCalledWith(stocks[0]);
    });

    it('should not select on Enter when nothing is highlighted', () => {
      const emitSpy = jest.spyOn(component.stockSelected, 'emit');
      component.highlightedIndex.set(-1);
      const event = new KeyboardEvent('keydown', {key: 'Enter'});
      component.onKeyDown(event);
      expect(emitSpy).not.toHaveBeenCalled();
    });
  });

  describe('onSelectStock', () => {
    it('should emit selected stock and reset state', () => {
      const emitSpy = jest.spyOn(component.stockSelected, 'emit');
      const stock: IndexedKeyTicker = {key_ticker: 'AAPL', index: 'nasdaq_100', name: 'Apple Inc'};

      component.searchQuery.set('AAPL');
      component.isOpen.set(true);
      component.highlightedIndex.set(0);

      component.onSelectStock(stock);

      expect(component.searchQuery()).toBe('');
      expect(component.isOpen()).toBe(false);
      expect(component.highlightedIndex()).toBe(-1);
      expect(emitSpy).toHaveBeenCalledWith(stock);
    });
  });

  describe('onClearSearch', () => {
    it('should reset search state', () => {
      component.searchQuery.set('test');
      component.isOpen.set(true);
      component.highlightedIndex.set(2);

      component.onClearSearch();

      expect(component.searchQuery()).toBe('');
      expect(component.isOpen()).toBe(false);
      expect(component.highlightedIndex()).toBe(-1);
    });
  });
});
