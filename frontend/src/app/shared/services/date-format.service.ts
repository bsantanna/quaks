import {inject, Injectable, PLATFORM_ID, signal, WritableSignal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {DateFormatName, DateFormatPreference, SharedStateService} from '../models/navigation.models';

@Injectable({
  providedIn: 'root',
})
export class DateFormatService implements SharedStateService<DateFormatPreference> {

  static readonly STORAGE_KEY = 'DateFormatPreference';
  static readonly DEFAULT_FORMAT: DateFormatName = 'DD/MM/YY';

  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  readonly state: WritableSignal<DateFormatPreference>;

  constructor() {
    const stored = this.isBrowser
      ? localStorage.getItem(DateFormatService.STORAGE_KEY)
      : null;

    this.state = signal<DateFormatPreference>(
      stored ? JSON.parse(stored) : {dateFormat: DateFormatService.DEFAULT_FORMAT}
    );
  }

  update(pref: DateFormatPreference): void {
    this.state.set(pref);
    if (this.isBrowser) {
      localStorage.setItem(DateFormatService.STORAGE_KEY, JSON.stringify(pref));
    }
  }

  format(value: string | null | undefined): string {
    if (!value) return '--';
    const parts = value.split('-');
    if (parts.length !== 3) return value;
    const [y, m, d] = parts;
    const yy = y.slice(2);
    switch (this.state().dateFormat) {
      case 'YY/MM/DD': return `${yy}/${m}/${d}`;
      case 'MM/DD/YY': return `${m}/${d}/${yy}`;
      case 'DD/MM/YY':
      default: return `${d}/${m}/${yy}`;
    }
  }

  toAngularFormat(): string {
    switch (this.state().dateFormat) {
      case 'YY/MM/DD': return 'yy/MM/dd';
      case 'MM/DD/YY': return 'MM/dd/yy';
      case 'DD/MM/YY':
      default: return 'dd/MM/yy';
    }
  }
}
