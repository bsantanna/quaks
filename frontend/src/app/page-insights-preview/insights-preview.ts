import {Component, computed, effect, inject, OnDestroy, PLATFORM_ID, signal} from '@angular/core';
import {ActivatedRoute, ParamMap} from '@angular/router';
import {isPlatformBrowser} from '@angular/common';
import {toSignal} from '@angular/core/rxjs-interop';
import {take} from 'rxjs';
import {MarketsInsightsService} from '../shared/services/markets-insights.service';
import {IndexedKeyTickerService} from '../shared/services/indexed-key-ticker.service';
import {DateFormatService, ShareUrlService, SeoService} from '../shared';
import {InsightsPreviewItem} from '../shared/models/markets.model';
import {
  applyInsightsAvatarFallback,
  ensureInsightsPrintStyle,
  formatInsightsDate,
  getInsightsAgentAvatarSrc,
  removeInsightsPrintStyle,
  sanitizeInsightsReportHtml,
} from '../shared/utils/content-format.utils';

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
            result.report_html = sanitizeInsightsReportHtml(result.report_html, this.getTickerSet());
            this.item.set(result);

            const title = result.executive_summary || 'Quaks Content Preview';
            const path = `/insights/preview/${docId}`;
            this.shareUrlService.update({
              title,
              url: `${globalThis.location.origin}${path}`,
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
    removeInsightsPrintStyle(document);
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
                result.report_html = sanitizeInsightsReportHtml(result.report_html, this.getTickerSet());
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

    ensureInsightsPrintStyle(document);
    const cleanup = () => removeInsightsPrintStyle(document);
    globalThis.addEventListener('afterprint', cleanup, {once: true});
    globalThis.print();
  }

  statusLabel(status: string): string {
    switch (status) {
      case 'pending': return 'Pending Review';
      case 'processed': return 'Published';
      case 'cancelled': return 'Cancelled';
      default: return status;
    }
  }

  agentAvatarSrc(skillName: string): string {
    return getInsightsAgentAvatarSrc(skillName);
  }

  onAvatarError(event: Event): void {
    applyInsightsAvatarFallback(event.target as HTMLImageElement);
  }

  formatDate(dateStr: string): string {
    return formatInsightsDate(dateStr, value => this.dateFormatService.format(value));
  }

  private getTickerSet(): Set<string> {
    this.tickerSet ??= new Set(
      this.tickerService.indexedKeyTickers().map(t => t.key_ticker)
    );
    return this.tickerSet;
  }
}
