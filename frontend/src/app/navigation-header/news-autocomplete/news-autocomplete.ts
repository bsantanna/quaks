import {Component, inject, input, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router} from '@angular/router';

@Component({
  selector: 'app-news-autocomplete',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './news-autocomplete.html',
  styleUrl: './news-autocomplete.scss',
})
export class NewsAutocompleteComponent {

  private readonly router = inject(Router);

  readonly inputPlaceholder = input('Search news');
  readonly searchQuery = signal('');
  readonly isOpen = signal(false);

  onSearch(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.searchQuery.set(target.value);
    this.isOpen.set(target.value.length > 0);
  }

  onInputFocus(): void {
    if (this.searchQuery().length > 0) {
      this.isOpen.set(true);
    }
  }

  onInputBlur(): void {
    setTimeout(() => {
      this.isOpen.set(false);
    }, 200);
  }

  onSearchSubmit(): void {
    const query = this.searchQuery().trim();
    if (query.length === 0) return;
    this.searchQuery.set('');
    this.isOpen.set(false);
    this.router.navigate(['/markets/news'], {queryParams: {search_term: query}});
  }

  onClearSearch(): void {
    this.searchQuery.set('');
    this.isOpen.set(false);
  }

}
