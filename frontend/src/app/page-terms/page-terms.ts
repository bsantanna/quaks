import {Component, inject} from '@angular/core';
import {SeoService} from '../shared';

@Component({
  selector: 'app-page-terms',
  imports: [],
  templateUrl: './page-terms.html',
  styleUrl: './page-terms.scss',
})
export class PageTerms {
  constructor() {
    inject(SeoService).update({
      title: 'Terms of Service',
      description: 'Terms of service and usage policies for the Quaks financial agents platform.',
      path: '/terms',
    });
  }
}
