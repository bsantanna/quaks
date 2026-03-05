import {Component, computed, effect, inject, OnDestroy} from '@angular/core';
import {ActivatedRoute, ParamMap} from '@angular/router';
import {ShareUrlService, MarketsNewsService, NewsItem} from '../shared';
import {toSignal} from '@angular/core/rxjs-interop';
import {take} from 'rxjs';
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

  sanitizeHtml(htmlContent: string | null | undefined): string {
    if (!htmlContent) {
      return '';
    }

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContent;

    // Remove dangerous elements
    tempDiv.querySelectorAll('script, style, iframe, noscript, object, embed, form, input, button').forEach(el => el.remove());

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

    return tempDiv.innerHTML;
  }

}
