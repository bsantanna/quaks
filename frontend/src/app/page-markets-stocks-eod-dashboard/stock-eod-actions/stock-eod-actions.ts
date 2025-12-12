import {Component, computed, input, signal, WritableSignal} from '@angular/core';
import {StockEodInsights} from '../stock-eod-insights/stock-eod-insights';
import {StockEodTools} from '../stock-eod-tools/stock-eod-tools';
import {SafeResourceUrl} from '@angular/platform-browser';

@Component({
  selector: 'app-stock-eod-actions',
  imports: [
    StockEodInsights,
    StockEodTools
  ],
  templateUrl: './stock-eod-actions.html',
  styleUrl: './stock-eod-actions.scss',
})
export class StockEodActions {

  readonly selectedTab: WritableSignal<string> = signal<string>('insights');

  readonly keyTicker = input.required<string>();

}
