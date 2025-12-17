import {Component, input} from '@angular/core';
import {DatePipe} from "@angular/common";
import {NewsItem} from '../../../models/markets.model';

@Component({
  selector: 'app-news-media-cards',
    imports: [
        DatePipe
    ],
  templateUrl: './news-media-cards.html',
  styleUrl: './news-media-cards.scss',
})
export class NewsMediaCards {

  readonly newsItems =  input.required<NewsItem[]>();

}
