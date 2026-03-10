import {Component, inject} from '@angular/core';
import {CookieConsentDialogComponent} from './cookie-consent-dialog/cookie-consent-dialog';
import {CookieService} from '../shared';

@Component({
  selector: 'app-navigation-footer',
  imports: [
    CookieConsentDialogComponent
  ],
  templateUrl: './navigation-footer.html',
  styleUrl: './navigation-footer.scss',
})
export class NavigationFooter {

  private readonly cookieService = inject(CookieService);

  manageCookies(): void {
    this.cookieService.resetConsent();
  }

}
