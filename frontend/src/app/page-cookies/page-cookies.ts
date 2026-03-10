import {Component, inject} from '@angular/core';
import {SeoService} from '../shared';

@Component({
  selector: 'app-page-cookies',
  imports: [],
  templateUrl: './page-cookies.html',
  styleUrl: './page-cookies.scss',
})
export class PageCookies {
  constructor() {
    inject(SeoService).update({
      title: 'Cookie Policy',
      description: 'Cookie policy for the Quaks quantitative finance platform.',
      path: '/cookies',
    });
  }
}
