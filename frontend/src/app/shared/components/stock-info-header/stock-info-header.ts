import {ChangeDetectorRef, Component, computed, effect, inject, input, model, Signal} from '@angular/core';
import {MarketsStatsService} from '../../services/markets-stats.service';
import {IndexedKeyTickerService} from '../../services/indexed-key-ticker.service';
import {DecimalPipe} from '@angular/common';
import {ShareUrlService} from '../../services/share-url.service';
import {take} from 'rxjs';
import {Router} from '@angular/router';
import {STOCK_EXCHANGE_FLAGS, STOCK_EXCHANGE_CURRENCY, STOCK_EXCHANGE_NAMES} from '../../../constants';

@Component({
  selector: 'app-stock-info-header',
  imports: [DecimalPipe],
  templateUrl: './stock-info-header.html',
  styleUrl: './stock-info-header.scss',
})
export class StockInfoHeader {

  private readonly router = inject(Router);
  private readonly marketsStatsService = inject(MarketsStatsService);
  private readonly shareUrlService = inject(ShareUrlService);
  private readonly indexedKeyTickerService = inject(IndexedKeyTickerService);
  private readonly cdr = inject(ChangeDetectorRef);
  readonly isStocksRoute = this.router.url.includes('/markets/stocks/');

  readonly indexName = input.required<string>();
  readonly keyTicker = input.required<string>();
  readonly companyName = input.required<string>();
  private readonly exchange = computed(() => this.indexedKeyTickerService.findKeyTicker(this.keyTicker())?.index ?? '');
  readonly exchangeFlag = computed(() => STOCK_EXCHANGE_FLAGS[this.exchange()] ?? '');
  readonly currencySymbol = computed(() => STOCK_EXCHANGE_CURRENCY[this.exchange()] ?? '');
  readonly exchangeName = computed(() => STOCK_EXCHANGE_NAMES[this.exchange()] ?? '');
  readonly intervalInDates = input.required<string>();
  readonly useIntervalInDates = input.required<boolean>();
  readonly intervalInDays = model.required<number>();

  readonly interval: Signal<string> = computed(() => {
    if (this.useIntervalInDates()) {
      return this.intervalInDates();
    }
    return `${this.getPastDateInDays(this.intervalInDays())}_${this.getPastDateInDays(1)}`;
  });

  readonly statsClose = this.marketsStatsService.statsClose;

  constructor() {
    effect(() => {
      this.marketsStatsService.getStatsClose(
        this.indexName(),
        this.keyTicker(),
        this.interval()
      ).pipe(take(1)).subscribe(stats => {
        this.marketsStatsService.statsClose.set(stats);
        this.cdr.markForCheck();
      });
    });
    effect(() => {
      this.exchangeFlag();
      this.currencySymbol();
      this.cdr.markForCheck();
    });
  }

  setIntervalInDays(days: number): void {
    this.intervalInDays.set(days);
  }

  getPastDateInDays(days: number): string {
    return this.shareUrlService.getPastDateInDays(days);
  }

  shortenDate(date: string): string {
    const [y, m, d] = date.split('-');
    return `${d}/${m}/${y.slice(2)}`;
  }

  formatVolume(value: number): string {
    if (value >= 1_000_000_000) return (value / 1_000_000_000).toFixed(2) + 'B';
    if (value >= 1_000_000) return (value / 1_000_000).toFixed(2) + 'M';
    if (value >= 1_000) return (value / 1_000).toFixed(1) + 'K';
    return value.toString();
  }

}
