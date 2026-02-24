import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter, Router} from '@angular/router';

import {NewsAutocompleteComponent} from './news-autocomplete';

describe('NewsAutocompleteComponent', () => {
  let component: NewsAutocompleteComponent;
  let fixture: ComponentFixture<NewsAutocompleteComponent>;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NewsAutocompleteComponent],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(NewsAutocompleteComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    jest.spyOn(router, 'navigate').mockResolvedValue(true);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with empty search query and closed dropdown', () => {
    expect(component.searchQuery()).toBe('');
    expect(component.isOpen()).toBe(false);
  });

  describe('onSearch', () => {
    it('should update search query and open dropdown', () => {
      const event = {target: {value: 'Tesla'}} as unknown as Event;
      component.onSearch(event);

      expect(component.searchQuery()).toBe('Tesla');
      expect(component.isOpen()).toBe(true);
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
      component.onInputBlur();

      setTimeout(() => {
        expect(component.isOpen()).toBe(false);
        done();
      }, 250);
    });
  });

  describe('onSearchSubmit', () => {
    it('should navigate to news page with search_term query param', () => {
      component.searchQuery.set('Bezos');

      component.onSearchSubmit();

      expect(router.navigate).toHaveBeenCalledWith(
        ['/markets/news'],
        {queryParams: {search_term: 'Bezos'}}
      );
      expect(component.searchQuery()).toBe('');
      expect(component.isOpen()).toBe(false);
    });

    it('should not navigate when search query is empty', () => {
      component.searchQuery.set('');

      component.onSearchSubmit();

      expect(router.navigate).not.toHaveBeenCalled();
    });

    it('should not navigate when search query is only whitespace', () => {
      component.searchQuery.set('   ');

      component.onSearchSubmit();

      expect(router.navigate).not.toHaveBeenCalled();
    });

    it('should trim the search query before navigating', () => {
      component.searchQuery.set('  Tesla  ');

      component.onSearchSubmit();

      expect(router.navigate).toHaveBeenCalledWith(
        ['/markets/news'],
        {queryParams: {search_term: 'Tesla'}}
      );
    });
  });

  describe('onClearSearch', () => {
    it('should reset search state', () => {
      component.searchQuery.set('test');
      component.isOpen.set(true);

      component.onClearSearch();

      expect(component.searchQuery()).toBe('');
      expect(component.isOpen()).toBe(false);
    });
  });
});
