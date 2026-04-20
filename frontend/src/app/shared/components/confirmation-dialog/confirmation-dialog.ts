import {Component, HostListener, input, output} from '@angular/core';

@Component({
  selector: 'app-confirmation-dialog',
  imports: [],
  templateUrl: './confirmation-dialog.html',
  styleUrl: './confirmation-dialog.scss',
})
export class ConfirmationDialog {
  readonly open = input.required<boolean>();
  readonly title = input<string>('Confirm');
  readonly message = input.required<string>();
  readonly okLabel = input<string>('OK');
  readonly cancelLabel = input<string>('Cancel');
  readonly variant = input<'primary' | 'danger'>('primary');

  readonly confirmed = output<void>();
  readonly cancelled = output<void>();

  onConfirm(): void {
    if (!this.open()) return;
    this.confirmed.emit();
  }

  onCancel(): void {
    if (!this.open()) return;
    this.cancelled.emit();
  }

  onBackdropClick(event: MouseEvent): void {
    if (event.target === event.currentTarget) {
      this.onCancel();
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.onCancel();
  }

  @HostListener('document:keydown.enter')
  onEnter(): void {
    this.onConfirm();
  }
}
