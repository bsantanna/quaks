import {AfterViewInit, Component, ElementRef, OnDestroy, signal, viewChild} from '@angular/core';
import {StockAutocompleteComponent} from './stock-autocomplete/stock-autocomplete';
import {IndexedKeyTicker} from '../shared/models/markets.model';
import {STOCK_MARKETS} from '../constants';
import {ShareButtonComponent} from './share-button/share-button';
import {NavButtonComponent} from './nav-button/nav-button';
import {FeedbackMessageComponent} from './feedback-message/feedback-message';
import {PathReactiveComponent} from '../shared/components/path-reactive.component';

@Component({
  selector: 'app-navigation-header',
  imports: [StockAutocompleteComponent, ShareButtonComponent, NavButtonComponent, FeedbackMessageComponent],
  templateUrl: './navigation-header.html',
  styleUrl: './navigation-header.scss',
})
export class NavigationHeader extends PathReactiveComponent implements AfterViewInit, OnDestroy {
  readonly subHeader = viewChild<ElementRef>('subHeader');
  readonly stickyVisible = signal(false);
  private observer: IntersectionObserver | null = null;

  onKeyTickerSelected(indexedKeyTicker: IndexedKeyTicker): void {
    if (STOCK_MARKETS.filter(market => market === indexedKeyTicker.index)) {
      this.router.navigate(['/markets/stocks', indexedKeyTicker.key_ticker]);
    }
  }

  ngAfterViewInit(): void {
    const el = this.subHeader()?.nativeElement;
    if (el) {
      this.observer = new IntersectionObserver(
        ([entry]) => this.stickyVisible.set(!entry.isIntersecting),
        {threshold: 0}
      );
      this.observer.observe(el);
    }
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }
}
