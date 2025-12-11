import {Component, input} from '@angular/core';

@Component({
  selector: 'app-stock-eod-insights',
  imports: [],
  templateUrl: './stock-eod-insights.html',
  styleUrl: './stock-eod-insights.scss',
})
export class StockEodInsights {

  readonly keyTicker = input.required<string>();

}
