import {inject, Injectable, Signal} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {IndexedKeyTicker} from '../models/markets.model';
import {toSignal} from '@angular/core/rxjs-interop';

@Injectable({
  providedIn: 'root',
})
export class IndexedKeyTickerService {

  private readonly httpClient = inject(HttpClient);
  readonly indexedKeyTickers!: Signal<IndexedKeyTicker[]>;

  constructor() {
    const indexedKeyTickers$ = this.httpClient.get<IndexedKeyTicker[]>('/json/indexed_key_ticker_list.json');
    this.indexedKeyTickers = toSignal(indexedKeyTickers$, {initialValue: []});
  }

  findKeyTicker(keyTicker: string): IndexedKeyTicker | null {
    return this.indexedKeyTickers().filter((i: IndexedKeyTicker) => i.key_ticker === keyTicker).at(0) ?? null;
  }

}
