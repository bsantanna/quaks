import {Component, input} from '@angular/core';
import {PathReactiveComponent} from '../../path-reactive.component';

@Component({
  selector: 'app-stock-eod-tools',
  imports: [],
  templateUrl: './stock-eod-tools.html',
  styleUrl: './stock-eod-tools.scss',
})
export class StockEodTools extends PathReactiveComponent {

  readonly keyTicker = input.required<string>();

}
