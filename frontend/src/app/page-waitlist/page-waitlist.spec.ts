import {ComponentFixture, TestBed} from '@angular/core/testing';
import {PageWaitlist} from './page-waitlist';
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {provideRouter} from '@angular/router';

describe('PageWaitlist', () => {
  let component: PageWaitlist;
  let fixture: ComponentFixture<PageWaitlist>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PageWaitlist],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PageWaitlist);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start in form state', () => {
    expect(component.state()).toBe('form');
  });

  it('should have invalid form when empty', () => {
    expect(component.form.invalid).toBe(true);
  });

  it('should validate email format', () => {
    component.form.controls.email.setValue('invalid');
    expect(component.form.controls.email.invalid).toBe(true);

    component.form.controls.email.setValue('test@example.com');
    expect(component.form.controls.email.valid).toBe(true);
  });

  it('should validate username minimum length', () => {
    component.form.controls.username.setValue('ab');
    expect(component.form.controls.username.invalid).toBe(true);

    component.form.controls.username.setValue('abc');
    expect(component.form.controls.username.valid).toBe(true);
  });

  it('should not submit when form is invalid', () => {
    component.submit();
    expect(component.submitting()).toBe(false);
    expect(component.state()).toBe('form');
  });
});
