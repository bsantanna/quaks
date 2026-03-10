import {Component, inject, input} from '@angular/core';
import {DatePipe} from '@angular/common';
import {NewsItem} from '../../../models/markets.model';
import {DateFormatService} from '../../../services/date-format.service';

@Component({
  selector: 'app-news-media-cards',
  imports: [DatePipe],
  templateUrl: './news-media-cards.html',
  styleUrl: './news-media-cards.scss',
})
export class NewsMediaCards {

  readonly dateFormatService = inject(DateFormatService);
  readonly newsItems = input.required<NewsItem[]>();
  readonly indexName = input.required<string>();

}
