import {Component, computed, effect, inject, OnDestroy, PLATFORM_ID, signal} from '@angular/core';
import {ActivatedRoute, ParamMap} from '@angular/router';
import {isPlatformBrowser} from '@angular/common';
import {toSignal} from '@angular/core/rxjs-interop';
import {take} from 'rxjs';
import {MarketsInsightsService} from '../shared/services/markets-insights.service';
import {IndexedKeyTickerService} from '../shared/services/indexed-key-ticker.service';
import {DateFormatService, ShareUrlService, SeoService} from '../shared';
import {InsightsPreviewItem} from '../shared/models/markets.model';

@Component({
  selector: 'app-insights-preview',
  imports: [],
  templateUrl: './insights-preview.html',
  styleUrl: './insights-preview.scss',
})
export class InsightsPreview implements OnDestroy {

  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly insightsService = inject(MarketsInsightsService);
  private readonly tickerService = inject(IndexedKeyTickerService);
  private readonly shareUrlService = inject(ShareUrlService);
  private readonly seoService = inject(SeoService);
  readonly dateFormatService = inject(DateFormatService);
  private tickerSet: Set<string> | null = null;

  private readonly paramMap = toSignal<ParamMap>(this.route.paramMap);
  readonly docId = computed(() => this.paramMap()?.get('docId') ?? '');
  readonly item = signal<InsightsPreviewItem | null>(null);
  readonly loading = signal(true);
  readonly cancelling = signal(false);
  readonly cancelError = signal(false);

  constructor() {
    effect(() => {
      const docId = this.docId();
      if (!docId || !this.isBrowser) return;

      this.insightsService.getInsightsPreview(docId)
        .pipe(take(1))
        .subscribe(result => {
          if (result) {
            result.report_html = this.sanitizeHtml(result.report_html);
            this.item.set(result);

            const title = result.executive_summary || 'Quaks Content Preview';
            const path = `/insights/preview/${docId}`;
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
    this.removePrintStyle();
  }

  cancelDocument(): void {
    const docId = this.docId();
    if (!docId || this.cancelling()) return;

    this.cancelling.set(true);
    this.cancelError.set(false);
    this.insightsService.cancelInsightsPreview(docId)
      .pipe(take(1))
      .subscribe({
        next: () => {
          this.insightsService.getInsightsPreview(docId)
            .pipe(take(1))
            .subscribe(result => {
              if (result) {
                result.report_html = this.sanitizeHtml(result.report_html);
                this.item.set(result);
              }
              this.cancelling.set(false);
            });
        },
        error: () => {
          this.cancelError.set(true);
          this.cancelling.set(false);
        }
      });
  }

  downloadPdf(): void {
    if (!this.isBrowser) return;

    const styleId = 'quaks-print-style';
    if (!document.getElementById(styleId)) {
      const style = document.createElement('style');
      style.id = styleId;
      style.textContent = `
        @media print {
          body > *:not(app-root) { display: none !important; }
          app-root > *:not(router-outlet):not(app-insights-preview) { display: none !important; }
          .print-hide { display: none !important; }
          .print-cover { display: block !important; }
          .briefing-report { border: none !important; }
          .briefing-card { border: none !important; border-radius: 0 !important; }
          @page {
            margin: 2cm 2.5cm;
            size: A4;
          }
        }
      `;
      document.head.appendChild(style);
    }

    const cleanup = () => this.removePrintStyle();
    window.addEventListener('afterprint', cleanup, {once: true});
    window.print();
  }

  private removePrintStyle(): void {
    const style = document.getElementById('quaks-print-style');
    if (style) style.remove();
  }

  statusLabel(status: string): string {
    switch (status) {
      case 'pending': return 'Pending Review';
      case 'processed': return 'Published';
      case 'cancelled': return 'Cancelled';
      default: return status;
    }
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
