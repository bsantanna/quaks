import {Component, input, output, signal} from '@angular/core';

@Component({
  selector: 'app-stock-comparison-time',
  imports: [],
  templateUrl: './stock-comparison-time.html',
  styleUrl: './stock-comparison-time.scss',
})
export class StockComparisonTime {

  readonly intervalInDays = input.required<number>();
  readonly intervalInDaysChange = output<number>();

  readonly ranges = [
    {label: '3M', days: 90},
    {label: '6M', days: 180},
    {label: '9M', days: 270},
    {label: '1Y', days: 365},
  ];

  setInterval(days: number): void {
    this.intervalInDaysChange.emit(days);
  }

}
