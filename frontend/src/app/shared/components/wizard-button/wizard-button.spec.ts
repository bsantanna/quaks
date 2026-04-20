import {ComponentFixture, TestBed} from '@angular/core/testing';

import {WizardButton} from './wizard-button';

describe('WizardButton', () => {
  let component: WizardButton;
  let fixture: ComponentFixture<WizardButton>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WizardButton],
    }).compileComponents();

    fixture = TestBed.createComponent(WizardButton);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should apply primary class by default', () => {
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    expect(btn.classList.contains('wizard-button-primary')).toBe(true);
    expect(btn.type).toBe('button');
  });

  it('should apply secondary class when variant is secondary', () => {
    fixture.componentRef.setInput('variant', 'secondary');
    fixture.detectChanges();
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    expect(btn.classList.contains('wizard-button-secondary')).toBe(true);
    expect(btn.classList.contains('wizard-button-primary')).toBe(false);
  });

  it('should apply danger class when variant is danger', () => {
    fixture.componentRef.setInput('variant', 'danger');
    fixture.detectChanges();
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    expect(btn.classList.contains('wizard-button-danger')).toBe(true);
  });

  it('should set type to submit when type input is submit', () => {
    fixture.componentRef.setInput('type', 'submit');
    fixture.detectChanges();
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    expect(btn.type).toBe('submit');
  });

  it('should respect disabled input', () => {
    fixture.componentRef.setInput('disabled', true);
    fixture.detectChanges();
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    expect(btn.disabled).toBe(true);
  });

  it('should emit pressed on click when enabled', () => {
    const spy = jest.fn();
    component.pressed.subscribe(spy);
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    btn.click();
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it('should not emit pressed when disabled', () => {
    fixture.componentRef.setInput('disabled', true);
    fixture.detectChanges();
    const spy = jest.fn();
    component.pressed.subscribe(spy);
    component.onClick();
    expect(spy).not.toHaveBeenCalled();
  });
});
