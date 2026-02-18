import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {NavButtonComponent} from './nav-button';

describe('NavButton', () => {
  let component: NavButtonComponent;
  let fixture: ComponentFixture<NavButtonComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavButtonComponent],
      providers: [provideRouter([])],
    })
      .compileComponents();

    fixture = TestBed.createComponent(NavButtonComponent);
    fixture.componentRef.setInput('buttonLabel', 'Test');
    fixture.componentRef.setInput('buttonIcon', '/svg/icon-test.svg');
    fixture.componentRef.setInput('navigationPath', '/test');
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
