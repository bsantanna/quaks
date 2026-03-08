import {Component, computed, effect, inject, OnDestroy, PLATFORM_ID} from '@angular/core';
import {ActivatedRoute, ParamMap} from '@angular/router';
import {ShareUrlService, MarketsNewsService, NewsItem, IndexedKeyTickerService, SeoService} from '../shared';
import {toSignal} from '@angular/core/rxjs-interop';
import {take} from 'rxjs';
import {DatePipe, isPlatformBrowser} from '@angular/common';

@Component({
  selector: 'app-markets-news-item',
  imports: [
    DatePipe
  ],
  templateUrl: './markets-news-item.component.html',
  styleUrl: './markets-news-item.component.scss',
})
export class MarketsNewsItem implements OnDestroy {

  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly route = inject(ActivatedRoute);
  private readonly shareUrlService = inject(ShareUrlService);
  private readonly marketsNewsService = inject(MarketsNewsService);
  private readonly indexedKeyTickerService = inject(IndexedKeyTickerService);
  private readonly seoService = inject(SeoService);

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
        const item = newsList.items.at(0);
        const linkTitle = item?.headline ?? 'Breaking news';
        if (this.isBrowser) {
          this.shareUrlService.update({
            title: linkTitle,
            url: `${window.location.href.split('?')[0]}`
          });
        }
        const path = `/markets/news/item/${this.indexName()}/${this.newsItemId()}`;
        this.seoService.update({
          title: linkTitle,
          description: item?.summary ?? undefined,
          path,
          image: item?.images?.[0]?.url ?? undefined,
        });
        if (item) {
          this.seoService.setNewsArticleSchema({
            headline: item.headline,
            description: item.summary,
            datePublished: item.date,
            image: item.images?.[0]?.url,
            author: item.source,
            url: `https://quaks.ai${path}`,
          });
        }
      })
    });
  }

  ngOnDestroy(): void {
    this.shareUrlService.update({title: '', url: ''});
    this.seoService.reset();
  }

  sanitizeHtml(htmlContent: string | null | undefined): string {
    if (!htmlContent) {
      return '';
    }

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContent;

    // Remove dangerous elements
    tempDiv.querySelectorAll('script, style, iframe, noscript, object, embed, form, input, button').forEach(el => el.remove());

    // Build a set of known tickers for fast lookup
    const knownTickers = new Set(this.indexedKeyTickerService.indexedKeyTickers().map(t => t.key_ticker));

    // Remove event handler attributes and dangerous attributes from all elements
    tempDiv.querySelectorAll('*').forEach(el => {
      for (const attr of Array.from(el.attributes)) {
        if (attr.name.startsWith('on') || attr.name === 'srcdoc') {
          el.removeAttribute(attr.name);
        }
      }
      // Sanitize href to prevent javascript: URLs
      if (el.hasAttribute('href')) {
        const href = el.getAttribute('href') ?? '';
        if (href.trim().toLowerCase().startsWith('javascript:')) {
          el.removeAttribute('href');
        }
      }
    });

    // Transform ticker links to internal routes
    tempDiv.querySelectorAll('a[href]').forEach(el => {
      const href = el.getAttribute('href') ?? '';
      const text = (el.textContent ?? '').trim();

      // Extract ticker from href (e.g. https://www.benzinga.com/quote/AAPL → AAPL)
      const hrefMatch = href.match(/\/quote\/([A-Z]+)$/);
      const tickerFromHref = hrefMatch ? hrefMatch[1] : '';
      // Also check if the link text itself is a known ticker
      const ticker = knownTickers.has(tickerFromHref) ? tickerFromHref
        : knownTickers.has(text) ? text
        : '';

      if (ticker) {
        el.setAttribute('href', `/markets/stocks/${ticker}`);
      }
    });

    return tempDiv.innerHTML;
  }

}
