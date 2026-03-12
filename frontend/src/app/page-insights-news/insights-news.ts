import {Component, computed, inject, PLATFORM_ID, signal} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {MarketsInsightsService} from '../shared/services/markets-insights.service';
import {IndexedKeyTickerService} from '../shared/services/indexed-key-ticker.service';
import {DateFormatService} from '../shared/services/date-format.service';
import {InsightsNewsItem} from '../shared/models/markets.model';
import {take} from 'rxjs';

@Component({
  selector: 'app-insights-news',
  imports: [],
  templateUrl: './insights-news.html',
  styleUrl: './insights-news.scss',
})
export class InsightsNews {
  private readonly insightsService = inject(MarketsInsightsService);
  private readonly tickerService = inject(IndexedKeyTickerService);
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private tickerSet: Set<string> | null = null;

  readonly dateFormatService = inject(DateFormatService);
  readonly items = signal<InsightsNewsItem[]>([]);
  readonly cursor = signal<string | null>(null);
  readonly loading = signal(false);
  readonly expandedId = signal<string | null>(null);
  readonly loadingReport = signal<string | null>(null);
  readonly hasMore = computed(() => this.cursor() !== null);

  private readonly indexName = 'quaks_insights-news_latest';
  private readonly pageSize = 10;

  constructor() {
    if (this.isBrowser) {
      this.fetchList('');
    }
  }

  loadMore(): void {
    const currentCursor = this.cursor();
    if (currentCursor === null || this.loading()) return;
    this.fetchList(currentCursor);
  }

  toggleReport(item: InsightsNewsItem): void {
    if (this.expandedId() === item.id) {
      this.expandedId.set(null);
      return;
    }

    if (item.report_html) {
      this.expandedId.set(item.id);
      return;
    }

    this.loadingReport.set(item.id);
    this.insightsService.getInsightsNewsItem(this.indexName, item.id)
      .pipe(take(1))
      .subscribe(result => {
        if (result.items.length > 0) {
          const fetched = result.items[0];
          const sanitized = this.sanitizeHtml(fetched.report_html);
          this.items.update(current =>
            current.map(i => i.id === item.id ? {...i, report_html: sanitized} : i)
          );
        }
        this.expandedId.set(item.id);
        this.loadingReport.set(null);
      });
  }

  private sanitizeHtml(html: string | null): string | null {
    if (!html) return html;
    let clean = html
      .replace(/<script[\s\S]*?<\/script>/gi, '')
      .replace(/<script[\s\S]*?\/>/gi, '')
      .replace(/\bon\w+\s*=\s*"[^"]*"/gi, '')
      .replace(/\bon\w+\s*=\s*'[^']*'/gi, '');

    // If content has no HTML block tags, it's plain text — add structure
    if (!/<(h[1-6]|p|div|ul|ol|table|section|article)\b/i.test(clean)) {
      clean = this.structurePlainText(clean);
    }

    clean = this.linkifyTickers(clean);

    return clean;
  }

  private structurePlainText(text: string): string {
    // Strip any stray tags, normalize line breaks
    const raw = text.replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, '');
    const lines = raw.split(/\n/).map(l => l.trim()).filter(l => l.length > 0);
    if (lines.length === 0) return '';

    const parts: string[] = [];

    // First line is the title
    parts.push(`<h2>${lines[0]}</h2>`);

    // Second line is often a subtitle/lede if it's short
    let start = 1;
    if (lines.length > 2 && lines[1].length < 200) {
      parts.push(`<p class="report-lede"><em>${lines[1]}</em></p>`);
      start = 2;
    }

    // Group remaining lines into paragraphs
    for (let i = start; i < lines.length; i++) {
      const line = lines[i];
      // Detect section headers: short lines (under 80 chars) that end without punctuation
      // or lines that are ALL CAPS or Title-Like
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

    // Match parenthesized uppercase symbols: (AAPL), (NVDA), (A)
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

  formatDate(dateStr: string): string {
    if (!dateStr) return '--';
    // Extract yyyy-mm-dd portion for DateFormatService
    const datePart = dateStr.substring(0, 10);
    return this.dateFormatService.format(datePart);
  }

  formatTime(dateStr: string): string {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  private fetchList(cursor: string): void {
    this.loading.set(true);
    this.insightsService.getInsightsNewsList(this.indexName, this.pageSize, cursor)
      .pipe(take(1))
      .subscribe(result => {
        this.items.update(current => [...current, ...result.items]);
        this.cursor.set(result.cursor);
        this.loading.set(false);
      });
  }
}
