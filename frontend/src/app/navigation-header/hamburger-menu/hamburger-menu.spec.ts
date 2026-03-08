import {ComponentFixture, TestBed} from '@angular/core/testing';
import {HamburgerMenuComponent} from './hamburger-menu';
import {provideRouter} from '@angular/router';
import {provideHttpClient} from '@angular/common/http';
import {ComponentRef} from '@angular/core';

describe('HamburgerMenuComponent', () => {
  let component: HamburgerMenuComponent;
  let componentRef: ComponentRef<HamburgerMenuComponent>;
  let fixture: ComponentFixture<HamburgerMenuComponent>;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [HamburgerMenuComponent],
      providers: [provideRouter([]), provideHttpClient()],
    }).compileComponents();

    fixture = TestBed.createComponent(HamburgerMenuComponent);
    component = fixture.componentInstance;
    componentRef = fixture.componentRef;
    componentRef.setInput('path', 'stocks');
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should toggle menu', () => {
    expect(component.menuOpen()).toBe(false);
    component.toggle();
    expect(component.menuOpen()).toBe(true);
    component.toggle();
    expect(component.menuOpen()).toBe(false);
  });

  it('should close menu', () => {
    component.menuOpen.set(true);
    component.close();
    expect(component.menuOpen()).toBe(false);
  });

  it('should select theme without closing menu', () => {
    component.menuOpen.set(true);
    component.selectTheme('bloomnerd');
    expect(component.themeService.state().theme).toBe('bloomnerd');
    expect(component.menuOpen()).toBe(true);
  });
});
