import {ComponentFixture, TestBed} from '@angular/core/testing';
import {signal} from '@angular/core';
import {IndexedKeyTickerService} from '../../shared';
import {StockComparisonAutocomplete} from './stock-comparison-autocomplete';

const MOCK_TICKERS = [
  {key_ticker: 'AAPL', index: 'nasdaq', name: 'Apple Inc.'},
  {key_ticker: 'MSFT', index: 'nasdaq', name: 'Microsoft Corporation'},
  {key_ticker: 'GOOGL', index: 'nasdaq', name: 'Alphabet Inc.'},
  {key_ticker: 'AMZN', index: 'nasdaq', name: 'Amazon.com Inc.'},
];

describe('StockComparisonAutocomplete', () => {
  let component: StockComparisonAutocomplete;
  let fixture: ComponentFixture<StockComparisonAutocomplete>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockComparisonAutocomplete],
      providers: [
        {
          provide: IndexedKeyTickerService,
          useValue: {indexedKeyTickers: signal(MOCK_TICKERS)},
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(StockComparisonAutocomplete);
    fixture.componentRef.setInput('symbols', []);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should filter stocks based on search query', () => {
    component.searchQuery.set('app');
    expect(component.filteredStocks().length).toBe(1);
    expect(component.filteredStocks()[0].key_ticker).toBe('AAPL');
  });

  it('should exclude already selected symbols from results', () => {
    fixture.componentRef.setInput('symbols', ['AAPL']);
    fixture.detectChanges();
    component.searchQuery.set('a');
    expect(component.filteredStocks().map(s => s.key_ticker)).not.toContain('AAPL');
  });

  it('should return empty when search query is empty', () => {
    component.searchQuery.set('');
    expect(component.filteredStocks()).toEqual([]);
  });

  it('should emit symbolsChange when adding a symbol', () => {
    const spy = jest.fn();
    component.symbolsChange.subscribe(spy);
    component.addSymbol(MOCK_TICKERS[0]);
    expect(spy).toHaveBeenCalledWith(['AAPL']);
  });

  it('should not emit duplicate symbol on add', () => {
    fixture.componentRef.setInput('symbols', ['AAPL']);
    fixture.detectChanges();
    const spy = jest.fn();
    component.symbolsChange.subscribe(spy);
    component.addSymbol(MOCK_TICKERS[0]);
    expect(spy).not.toHaveBeenCalled();
  });

  it('should emit symbolsChange when removing a symbol', () => {
    fixture.componentRef.setInput('symbols', ['AAPL', 'MSFT']);
    fixture.detectChanges();
    const spy = jest.fn();
    component.symbolsChange.subscribe(spy);
    component.removeSymbol('AAPL');
    expect(spy).toHaveBeenCalledWith(['MSFT']);
  });

  it('should clear search and close dropdown after adding', () => {
    component.searchQuery.set('app');
    component.isOpen.set(true);
    component.addSymbol(MOCK_TICKERS[0]);
    expect(component.searchQuery()).toBe('');
    expect(component.isOpen()).toBe(false);
  });

  it('should open dropdown on search input', () => {
    const event = {target: {value: 'goo'}} as unknown as Event;
    component.onSearch(event);
    expect(component.searchQuery()).toBe('goo');
    expect(component.isOpen()).toBe(true);
  });

  it('should close dropdown on empty input', () => {
    const event = {target: {value: ''}} as unknown as Event;
    component.onSearch(event);
    expect(component.isOpen()).toBe(false);
  });

  it('should open on focus if query exists', () => {
    component.searchQuery.set('test');
    component.onInputFocus();
    expect(component.isOpen()).toBe(true);
  });

  it('should not open on focus if query is empty', () => {
    component.searchQuery.set('');
    component.onInputFocus();
    expect(component.isOpen()).toBe(false);
  });

  it('should clear search on onClearSearch', () => {
    component.searchQuery.set('test');
    component.isOpen.set(true);
    component.onClearSearch();
    expect(component.searchQuery()).toBe('');
    expect(component.isOpen()).toBe(false);
    expect(component.highlightedIndex()).toBe(-1);
  });

  it('should navigate highlighted index with ArrowDown', () => {
    component.searchQuery.set('a');
    component.isOpen.set(true);
    const event = {key: 'ArrowDown', preventDefault: jest.fn()} as unknown as KeyboardEvent;
    component.onKeyDown(event);
    expect(component.highlightedIndex()).toBe(0);
    expect(event.preventDefault).toHaveBeenCalled();
  });

  it('should navigate highlighted index with ArrowUp', () => {
    component.searchQuery.set('a');
    component.isOpen.set(true);
    component.highlightedIndex.set(1);
    const event = {key: 'ArrowUp', preventDefault: jest.fn()} as unknown as KeyboardEvent;
    component.onKeyDown(event);
    expect(component.highlightedIndex()).toBe(0);
  });

  it('should close dropdown and reset on blur', () => {
    jest.useFakeTimers();
    component.isOpen.set(true);
    component.highlightedIndex.set(2);
    component.onInputBlur();
    jest.advanceTimersByTime(200);
    expect(component.isOpen()).toBe(false);
    expect(component.highlightedIndex()).toBe(-1);
    jest.useRealTimers();
  });

  it('should do nothing on keydown when dropdown is closed', () => {
    component.isOpen.set(false);
    const event = {key: 'ArrowDown', preventDefault: jest.fn()} as unknown as KeyboardEvent;
    component.onKeyDown(event);
    expect(event.preventDefault).not.toHaveBeenCalled();
  });

  it('should select highlighted item on Enter', () => {
    component.searchQuery.set('a');
    component.isOpen.set(true);
    component.highlightedIndex.set(0);
    const spy = jest.fn();
    component.symbolsChange.subscribe(spy);
    const event = {key: 'Enter', preventDefault: jest.fn()} as unknown as KeyboardEvent;
    component.onKeyDown(event);
    expect(spy).toHaveBeenCalled();
  });
});
