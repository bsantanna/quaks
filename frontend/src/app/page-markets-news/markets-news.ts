import { Component } from '@angular/core';
import { NewsFeed } from '../shared/components/news-feed/news-feed.component';

@Component({
  selector: 'app-markets-news',
  imports: [NewsFeed],
  templateUrl: './markets-news.html',
  styleUrl: './markets-news.scss',
})
export class MarketsNews {

}
