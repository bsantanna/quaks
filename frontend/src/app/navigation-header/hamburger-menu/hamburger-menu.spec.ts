import {ComponentFixture, TestBed} from '@angular/core/testing';
import {HamburgerMenuComponent} from './hamburger-menu';
import {provideHttpClient} from '@angular/common/http';
import {ComponentRef, signal} from '@angular/core';
import {Router} from '@angular/router';
import {AuthService} from '../../shared/services/auth.service';

describe('HamburgerMenuComponent', () => {
  let component: HamburgerMenuComponent;
  let componentRef: ComponentRef<HamburgerMenuComponent>;
  let fixture: ComponentFixture<HamburgerMenuComponent>;
  const router = {
    navigate: jest.fn(),
  };
  const authService = {
    state: signal(null),
    isLoggedIn: signal(false),
    subscriptionTier: signal('free' as const),
    initiateLogin: jest.fn(),
    logout: jest.fn(),
    getAccessToken: jest.fn().mockReturnValue(null),
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [HamburgerMenuComponent],
      providers: [
        provideHttpClient(),
        {provide: Router, useValue: router},
        {provide: AuthService, useValue: authService},
      ],
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

  it('navigates and closes the menu', () => {
    component.menuOpen.set(true);
    component.themeOpen.set(true);

    component.navigate('/markets/stocks');

    expect(router.navigate).toHaveBeenCalledWith(['/markets/stocks']);
    expect(component.menuOpen()).toBe(false);
    expect(component.themeOpen()).toBe(false);
  });

  it('updates the date format without closing the menu', () => {
    component.menuOpen.set(true);

    component.selectDateFormat('YY/MM/DD');

    expect(component.dateFormatService.state().dateFormat).toBe('YY/MM/DD');
    expect(component.menuOpen()).toBe(true);
  });

  it('handles login and logout through the auth service', () => {
    component.menuOpen.set(true);
    component.login();
    expect(authService.initiateLogin).toHaveBeenCalled();
    expect(component.menuOpen()).toBe(false);

    component.menuOpen.set(true);
    component.logout();
    expect(authService.logout).toHaveBeenCalled();
    expect(component.menuOpen()).toBe(false);
  });

  it('emits only for supported stock indexes', () => {
    const emitSpy = jest.fn();
    component.stockSelected.subscribe(emitSpy);
    component.menuOpen.set(true);

    component.onKeyTickerSelected({key_ticker: 'AAPL', index: 'nasdaq', name: 'Apple'});
    expect(emitSpy).toHaveBeenCalledWith({key_ticker: 'AAPL', index: 'nasdaq', name: 'Apple'});
    expect(component.menuOpen()).toBe(false);

    component.menuOpen.set(true);
    component.onKeyTickerSelected({key_ticker: 'BTC', index: 'crypto', name: 'Bitcoin'});
    expect(emitSpy).toHaveBeenCalledTimes(1);
    expect(component.menuOpen()).toBe(true);
  });
});
