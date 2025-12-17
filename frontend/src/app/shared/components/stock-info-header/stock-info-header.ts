import {Component, computed, effect, inject, input, model, Signal, signal, WritableSignal} from '@angular/core';
import {MarketsStatsService} from '../../services/markets-stats.service';
import {StatsClose} from '../../models/markets.model';
import {DecimalPipe} from '@angular/common';
import {ShareUrlService} from '../../services/share-url.service';
import {take} from 'rxjs';
import {PathReactiveComponent} from '../path-reactive.component';

@Component({
  selector: 'app-stock-info-header',
  imports: [DecimalPipe],
  templateUrl: './stock-info-header.html',
  styleUrl: './stock-info-header.scss',
})
export class StockInfoHeader extends PathReactiveComponent {

  private readonly marketsStatsService = inject(MarketsStatsService);
  private readonly shareUrlService = inject(ShareUrlService);

  readonly indexName = input.required<string>();
  readonly keyTicker = input.required<string>();
  readonly companyName = input.required<string>();
  readonly intervalInDates = input.required<string>();
  readonly useIntervalInDates = input.required<boolean>();
  readonly intervalInDays = model.required<number>();

  private readonly interval: Signal<string> = computed(() => {
    if (this.useIntervalInDates()) {
      return this.intervalInDates();
    }
    return `${this.getPastDateInDays(this.intervalInDays())}_${this.getPastDateInDays(1)}`;
  });

  readonly statsClose = this.marketsStatsService.statsClose;

  constructor() {
    super();
    effect(() => {
      this.marketsStatsService.getStatsClose(
        this.indexName(),
        this.keyTicker(),
        this.interval()
      ).pipe(take(1)).subscribe(stats => {
        this.marketsStatsService.statsClose.set(stats);
      });
    });
  }

  setIntervalInDays(days: number): void {
    this.intervalInDays.set(days);
  }

  getPastDateInDays(days: number): string {
    return this.shareUrlService.getPastDateInDays(days);
  }

}
