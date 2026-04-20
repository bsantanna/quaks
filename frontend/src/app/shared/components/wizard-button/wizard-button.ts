import {Component, input, output} from '@angular/core';

@Component({
  selector: 'app-wizard-button',
  imports: [],
  templateUrl: './wizard-button.html',
  styleUrl: './wizard-button.scss',
})
export class WizardButton {
  readonly variant = input<'primary' | 'secondary' | 'danger'>('primary');
  readonly type = input<'button' | 'submit'>('button');
  readonly disabled = input<boolean>(false);

  readonly pressed = output<void>();

  onClick(): void {
    if (this.disabled()) return;
    this.pressed.emit();
  }
}
