import {Component, computed, effect, inject, OnDestroy} from '@angular/core';
import {ActivatedRoute, ParamMap} from '@angular/router';
import {ShareUrlService} from '../shared/services/share-url.service';
import {toSignal} from '@angular/core/rxjs-interop';
import {MarketsNewsService} from '../shared/services/markets-news.service';
import {take} from 'rxjs';
import {NewsItem} from '../shared/models/markets.model';
import {DatePipe} from '@angular/common';

@Component({
  selector: 'app-markets-news-item',
  imports: [
    DatePipe
  ],
  templateUrl: './markets-news-item.component.html',
  styleUrl: './markets-news-item.component.scss',
})
export class MarketsNewsItem implements OnDestroy {

  private readonly route = inject(ActivatedRoute);
  private readonly shareUrlService = inject(ShareUrlService);
  private readonly marketsNewsService = inject(MarketsNewsService);

  private readonly paramMap = toSignal<ParamMap>(this.route.paramMap);
  readonly indexName = computed(() => this.paramMap()?.get('indexName') ?? '');
  readonly newsItemId = computed(() => this.paramMap()?.get('newsItemId') ?? '');
  readonly newsList = this.marketsNewsService.newsList;
  readonly newsItem = computed(() => this.newsList().items.at(0) as NewsItem);

  constructor() {
    effect(() => {
      this.marketsNewsService.getNewsItem(
        this.indexName(),
        this.newsItemId()
      ).pipe(take(1)).subscribe(newsList => {
        this.marketsNewsService.newsList.set(newsList);
        const linkTitle = newsList.items.at(0)?.headline ?? 'Breaking news';
        this.shareUrlService.update({
          title: linkTitle,
          url: `${window.location.href.split('?')[0]}`
        });
      })
    });
  }

  ngOnDestroy(): void {
    this.shareUrlService.update({title: '', url: ''});
  }

  sanitizeHtmlToPlainText(htmlContent: string | null | undefined): string {
    if (!htmlContent) {
      return '';
    }

    // Step 1: Create a temporary DOM element to parse the HTML
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContent;

    // Step 2: Remove dangerous elements (scripts, styles, iframes, etc.)
    tempDiv.querySelectorAll('script, style, iframe, noscript').forEach(el => el.remove());

    // Step 3: Extract text content
    let text = tempDiv.textContent || tempDiv.innerText || '';

    // Step 4: Normalize whitespace and line breaks
    text = text
      .replace(/\s+/g, ' ')           // Collapse multiple spaces/tabs into one
      .replace(/ (\n|\r\n?)/g, '\n')  // Remove spaces before newlines
      .trim();

    // Step 5: Split into paragraphs based on double newlines (common in extracted text)
    const paragraphs = text
      .split(/\n\s*\n/)               // Split on blank lines
      .map(p => p.trim())
      .filter(p => p.length > 0);

    // Step 6: Join paragraphs with double newlines for natural spacing
    return paragraphs.join('\n\n');
  }

}
