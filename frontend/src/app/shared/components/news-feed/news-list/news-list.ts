import {Component, input} from '@angular/core';
import {DatePipe} from "@angular/common";
import {NewsItem} from '../../../models/markets.model';

@Component({
  selector: 'app-news-list',
    imports: [
        DatePipe
    ],
  templateUrl: './news-list.html',
  styleUrl: './news-list.scss',
})
export class NewsList {

  readonly newsItems =  input.required<NewsItem[]>();
  readonly indexName = input.required<string>();

}
