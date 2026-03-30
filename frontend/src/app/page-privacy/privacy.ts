import {Component, inject} from '@angular/core';
import {SeoService} from '../shared';

@Component({
  selector: 'app-privacy',
  imports: [],
  templateUrl: './privacy.html',
  styleUrl: './privacy.scss',
})
export class Privacy {
constructor() {
    inject(SeoService).update({
      title: 'Privacy Policy',
      description: 'Privacy policy for the Quaks quantitative finance platform.',
      path: '/privacy',
    });
  }
}
