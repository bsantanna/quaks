import {Component} from '@angular/core';
import {StockAutocompleteComponent} from './stock-autocomplete/stock-autocomplete';
import {IndexedKeyTicker} from '../shared/models/markets.model';
import {STOCK_MARKETS} from '../constants';
import {ShareButtonComponent} from './share-button/share-button';
import {FeedbackMessageComponent} from './feedback-message/feedback-message';
import {PathReactiveComponent} from '../shared/components/path-reactive.component';

@Component({
  selector: 'app-navigation-header',
  imports: [StockAutocompleteComponent, ShareButtonComponent, FeedbackMessageComponent],
  templateUrl: './navigation-header.html',
  styleUrl: './navigation-header.scss',
})
export class NavigationHeader extends PathReactiveComponent {

  onKeyTickerSelected(indexedKeyTicker: IndexedKeyTicker): void {
    if (STOCK_MARKETS.filter(market => market === indexedKeyTicker.index)) {
      this.router.navigate(['/markets/stocks', indexedKeyTicker.key_ticker]);
    }
  }

}
