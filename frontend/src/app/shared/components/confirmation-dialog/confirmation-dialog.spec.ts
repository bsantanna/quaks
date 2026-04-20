import {ComponentFixture, TestBed} from '@angular/core/testing';

import {ConfirmationDialog} from './confirmation-dialog';

describe('ConfirmationDialog', () => {
  let component: ConfirmationDialog;
  let fixture: ComponentFixture<ConfirmationDialog>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConfirmationDialog],
    }).compileComponents();

    fixture = TestBed.createComponent(ConfirmationDialog);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('open', true);
    fixture.componentRef.setInput('message', 'Are you sure?');
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render default title, message, and labels', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.confirmation-title')?.textContent).toContain('Confirm');
    expect(el.querySelector('.confirmation-message')?.textContent).toContain('Are you sure?');
    expect(el.querySelector('.confirmation-btn-primary')?.textContent).toContain('OK');
    expect(el.querySelector('.confirmation-btn-secondary')?.textContent).toContain('Cancel');
  });

  it('should render custom title and labels', () => {
    fixture.componentRef.setInput('title', 'Reset agent?');
    fixture.componentRef.setInput('okLabel', 'Reset');
    fixture.componentRef.setInput('cancelLabel', 'Keep');
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.confirmation-title')?.textContent).toContain('Reset agent?');
    expect(el.querySelector('.confirmation-btn-primary')?.textContent).toContain('Reset');
    expect(el.querySelector('.confirmation-btn-secondary')?.textContent).toContain('Keep');
  });

  it('should not render when open is false', () => {
    fixture.componentRef.setInput('open', false);
    fixture.detectChanges();
    const backdrop = fixture.nativeElement.querySelector('.confirmation-backdrop');
    expect(backdrop).toBeNull();
  });

  it('should emit confirmed on OK click', () => {
    const spy = jest.fn();
    component.confirmed.subscribe(spy);
    const okBtn: HTMLButtonElement = fixture.nativeElement.querySelector('.confirmation-btn-primary');
    okBtn.click();
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it('should emit cancelled on Cancel click', () => {
    const spy = jest.fn();
    component.cancelled.subscribe(spy);
    const cancelBtn: HTMLButtonElement = fixture.nativeElement.querySelector('.confirmation-btn-secondary');
    cancelBtn.click();
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it('should emit cancelled on backdrop click', () => {
    const spy = jest.fn();
    component.cancelled.subscribe(spy);
    const backdrop: HTMLElement = fixture.nativeElement.querySelector('.confirmation-backdrop');
    const event = new MouseEvent('click', {bubbles: true});
    Object.defineProperty(event, 'target', {value: backdrop});
    Object.defineProperty(event, 'currentTarget', {value: backdrop});
    component.onBackdropClick(event);
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it('should not emit cancelled when clicking inside the panel', () => {
    const spy = jest.fn();
    component.cancelled.subscribe(spy);
    const backdrop: HTMLElement = fixture.nativeElement.querySelector('.confirmation-backdrop');
    const panel: HTMLElement = fixture.nativeElement.querySelector('.confirmation-panel');
    const event = new MouseEvent('click', {bubbles: true});
    Object.defineProperty(event, 'target', {value: panel});
    Object.defineProperty(event, 'currentTarget', {value: backdrop});
    component.onBackdropClick(event);
    expect(spy).not.toHaveBeenCalled();
  });

  it('should emit cancelled on ESC key', () => {
    const spy = jest.fn();
    component.cancelled.subscribe(spy);
    component.onEscape();
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it('should emit confirmed on Enter key', () => {
    const spy = jest.fn();
    component.confirmed.subscribe(spy);
    component.onEnter();
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it('should apply primary class by default', () => {
    const btns = fixture.nativeElement.querySelectorAll('.confirmation-btn');
    const okBtn: HTMLElement = btns[btns.length - 1];
    expect(okBtn.classList.contains('confirmation-btn-primary')).toBe(true);
    expect(okBtn.classList.contains('confirmation-btn-danger')).toBe(false);
  });

  it('should apply danger class when variant is danger', () => {
    fixture.componentRef.setInput('variant', 'danger');
    fixture.detectChanges();
    const btns = fixture.nativeElement.querySelectorAll('.confirmation-btn');
    const okBtn: HTMLElement = btns[btns.length - 1];
    expect(okBtn.classList.contains('confirmation-btn-danger')).toBe(true);
    expect(okBtn.classList.contains('confirmation-btn-primary')).toBe(false);
  });

  it('should not emit on keys when closed', () => {
    fixture.componentRef.setInput('open', false);
    fixture.detectChanges();
    const confirmSpy = jest.fn();
    const cancelSpy = jest.fn();
    component.confirmed.subscribe(confirmSpy);
    component.cancelled.subscribe(cancelSpy);
    component.onEscape();
    component.onEnter();
    expect(confirmSpy).not.toHaveBeenCalled();
    expect(cancelSpy).not.toHaveBeenCalled();
  });
});
