import {Component, input} from '@angular/core';

export interface WizardStep {
  id: number;
  displayId: number;
  label: string;
}

@Component({
  selector: 'app-wizard-stepper',
  imports: [],
  templateUrl: './wizard-stepper.html',
  styleUrl: './wizard-stepper.scss',
})
export class WizardStepper {
  readonly steps = input.required<readonly WizardStep[]>();
  readonly currentStep = input.required<number>();
  readonly ariaLabel = input<string>('Progress');
}
