import {ChangeDetectorRef, Component, effect, HostListener, inject, signal} from '@angular/core';
import {ShareUrlService, FeedbackMessageService} from '../../shared';
import {buildShareAction, SharePlatform} from '../../shared/utils/social-share.utils';

@Component({
  selector: 'app-share-button',
  imports: [],
  templateUrl: './share-button.html',
  styleUrl: './share-button.scss',
})
export class ShareButtonComponent {

  private readonly shareUrlService = inject(ShareUrlService);
  private readonly feedbackMessageService = inject(FeedbackMessageService);
  private readonly cdr = inject(ChangeDetectorRef);
  readonly shareUrl = this.shareUrlService.state;
  readonly showMenu = signal<boolean>(false);

  constructor() {
    effect(() => {
      this.shareUrl();
      this.cdr.markForCheck();
    });
  }

  toggleMenu() {
    this.showMenu.update((val) => !val);
  }

  share(platform: SharePlatform) {
    this.showMenu.set(false);
    const action = buildShareAction(platform, this.shareUrl());
    if (!action) return;

    if (action.kind === 'clipboard') {
      navigator.clipboard.writeText(action.text);
      this.feedbackMessageService.update({
        message: 'Link copied',
        type: 'info',
        timeout: 3000,
      });
      return;
    }

    if (action.kind === 'redirect') {
      window.location.href = action.targetUrl;
      return;
    }

    window.open(action.targetUrl, '_blank');
  }

  @HostListener('document:click', ['$event'])
  @HostListener('document:touchstart', ['$event'])
  onDocumentClick(event: Event) {
    const target = event.target as HTMLElement;
    if (!target.closest('app-share-button')) {
      this.showMenu.set(false);
    }
  }

}
