import {ComponentFixture, TestBed} from '@angular/core/testing';

import {WizardStepper} from './wizard-stepper';

describe('WizardStepper', () => {
  let component: WizardStepper;
  let fixture: ComponentFixture<WizardStepper>;

  const steps = [
    {id: 1, displayId: 1, label: 'Create'},
    {id: 2, displayId: 2, label: 'Configure'},
    {id: 3, displayId: 3, label: 'Review'},
    {id: 4, displayId: 4, label: 'Done'},
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WizardStepper],
    }).compileComponents();

    fixture = TestBed.createComponent(WizardStepper);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('steps', steps);
    fixture.componentRef.setInput('currentStep', 2);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render one item per step with correct displayId and label', () => {
    const items = fixture.nativeElement.querySelectorAll('.wizard-stepper-item');
    expect(items.length).toBe(4);
    expect(items[0].querySelector('.wizard-stepper-badge')?.textContent).toContain('1');
    expect(items[0].querySelector('.wizard-stepper-label')?.textContent).toContain('Create');
  });

  it('should mark current step as active', () => {
    const items = fixture.nativeElement.querySelectorAll('.wizard-stepper-item');
    expect(items[1].classList.contains('wizard-stepper-active')).toBe(true);
    expect(items[0].classList.contains('wizard-stepper-complete')).toBe(true);
    expect(items[2].classList.contains('wizard-stepper-active')).toBe(false);
  });

  it('should mark steps before current as complete', () => {
    const items = fixture.nativeElement.querySelectorAll('.wizard-stepper-item');
    expect(items[0].classList.contains('wizard-stepper-complete')).toBe(true);
    expect(items[2].classList.contains('wizard-stepper-complete')).toBe(false);
    expect(items[3].classList.contains('wizard-stepper-complete')).toBe(false);
  });

  it('should use custom aria-label when provided', () => {
    fixture.componentRef.setInput('ariaLabel', 'Setup progress');
    fixture.detectChanges();
    const ol: HTMLElement = fixture.nativeElement.querySelector('.wizard-stepper');
    expect(ol.getAttribute('aria-label')).toBe('Setup progress');
  });
});
