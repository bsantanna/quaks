import {Component, computed, effect, inject, OnDestroy, PLATFORM_ID, signal} from '@angular/core';
import {ActivatedRoute, ParamMap} from '@angular/router';
import {isPlatformBrowser} from '@angular/common';
import {toSignal} from '@angular/core/rxjs-interop';
import {take} from 'rxjs';
import {MarketsInsightsService} from '../shared/services/markets-insights.service';
import {IndexedKeyTickerService} from '../shared/services/indexed-key-ticker.service';
import {DateFormatService, ShareUrlService, SeoService} from '../shared';
import {InsightsNewsItem as InsightsNewsItemModel} from '../shared/models/markets.model';

@Component({
  selector: 'app-insights-news-item',
  imports: [],
  templateUrl: './insights-news-item.html',
  styleUrl: './insights-news-item.scss',
})
export class InsightsNewsItem implements OnDestroy {

  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly insightsService = inject(MarketsInsightsService);
  private readonly tickerService = inject(IndexedKeyTickerService);
  private readonly shareUrlService = inject(ShareUrlService);
  private readonly seoService = inject(SeoService);
  readonly dateFormatService = inject(DateFormatService);
  private tickerSet: Set<string> | null = null;

  private readonly paramMap = toSignal<ParamMap>(this.route.paramMap);
  readonly indexName = computed(() => this.paramMap()?.get('indexName') ?? '');
  readonly newsItemId = computed(() => this.paramMap()?.get('newsItemId') ?? '');
  readonly item = signal<InsightsNewsItemModel | null>(null);
  readonly loading = signal(true);

  constructor() {
    effect(() => {
      const indexName = this.indexName();
      const id = this.newsItemId();
      if (!indexName || !id || !this.isBrowser) return;

      this.insightsService.getInsightsNewsItem(indexName, id)
        .pipe(take(1))
        .subscribe(result => {
          if (result.items.length > 0) {
            const fetched = result.items[0];
            fetched.report_html = this.sanitizeHtml(fetched.report_html);
            this.item.set(fetched);

            const title = fetched.executive_summary || 'Quaks News Insight';
            const path = `/insights/news/item/${indexName}/${id}`;
            this.shareUrlService.update({
              title,
              url: `${window.location.origin}${path}`,
            });
            this.seoService.update({title, path});
          }
          this.loading.set(false);
        });
    });
  }

  ngOnDestroy(): void {
    this.shareUrlService.update({title: '', url: ''});
    this.seoService.reset();
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '--';
    return this.dateFormatService.format(dateStr.substring(0, 10));
  }

  sanitizeHtml(html: string | null): string | null {
    if (!html) return html;
    let clean = html
      .replace(/<script[\s\S]*?<\/script>/gi, '')
      .replace(/<script[\s\S]*?\/>/gi, '')
      .replace(/\bon\w+\s*=\s*"[^"]*"/gi, '')
      .replace(/\bon\w+\s*=\s*'[^']*'/gi, '');

    if (!/<(h[1-6]|p|div|ul|ol|table|section|article)\b/i.test(clean)) {
      clean = this.structurePlainText(clean);
    }

    clean = this.linkifyTickers(clean);
    return clean;
  }

  private structurePlainText(text: string): string {
    const raw = text.replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, '');
    const lines = raw.split(/\n/).map(l => l.trim()).filter(l => l.length > 0);
    if (lines.length === 0) return '';

    const parts: string[] = [];
    parts.push(`<h2>${lines[0]}</h2>`);

    let start = 1;
    if (lines.length > 2 && lines[1].length < 200) {
      parts.push(`<p class="report-lede"><em>${lines[1]}</em></p>`);
      start = 2;
    }

    for (let i = start; i < lines.length; i++) {
      const line = lines[i];
      const isHeader = line.length < 100
        && !line.endsWith('.')
        && !line.endsWith(',')
        && !line.endsWith(':')
        && !/\d+%/.test(line)
        && (
          line === line.toUpperCase()
          || /^[A-Z][^.]*[A-Z][^.]*$/.test(line)
          || line.includes('—')
          || line.includes(' — ')
        );

      if (isHeader) {
        parts.push(`<h3>${line}</h3>`);
      } else {
        parts.push(`<p>${line}</p>`);
      }
    }

    return parts.join('\n');
  }

  private getTickerSet(): Set<string> {
    if (!this.tickerSet) {
      this.tickerSet = new Set(
        this.tickerService.indexedKeyTickers().map(t => t.key_ticker)
      );
    }
    return this.tickerSet;
  }

  private linkifyTickers(html: string): string {
    const tickers = this.getTickerSet();
    if (tickers.size === 0) return html;

    return html.replace(
      /\(([A-Z]{1,5})\)/g,
      (match, ticker) => {
        if (tickers.has(ticker)) {
          return `(<a href="/markets/stocks/${ticker}" class="ticker-link">${ticker}</a>)`;
        }
        return match;
      }
    );
  }
}
