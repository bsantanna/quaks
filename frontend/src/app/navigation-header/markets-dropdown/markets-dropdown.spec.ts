import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideRouter, Router} from '@angular/router';
import {MarketsDropdownComponent} from './markets-dropdown';

describe('MarketsDropdownComponent', () => {
  let component: MarketsDropdownComponent;
  let fixture: ComponentFixture<MarketsDropdownComponent>;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsDropdownComponent],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(MarketsDropdownComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start with menu hidden', () => {
    expect(component.showMenu()).toBe(false);
  });

  it('should toggle menu open and closed', () => {
    component.toggleMenu();
    expect(component.showMenu()).toBe(true);
    component.toggleMenu();
    expect(component.showMenu()).toBe(false);
  });

  it('should navigate to path and close menu on navigate()', () => {
    const navigateSpy = jest.spyOn(router, 'navigate').mockResolvedValue(true);
    component.showMenu.set(true);

    component.navigate('/markets/stocks');

    expect(navigateSpy).toHaveBeenCalledWith(['/markets/stocks']);
    expect(component.showMenu()).toBe(false);
  });

  it('should close menu on document click outside component', () => {
    component.showMenu.set(true);
    const outsideDiv = document.createElement('div');
    component.onDocumentClick({target: outsideDiv} as unknown as Event);
    expect(component.showMenu()).toBe(false);
  });

  it('should keep menu open on document click inside component', () => {
    component.showMenu.set(true);
    const insideTarget = {
      closest: (selector: string) => selector === 'app-markets-dropdown' ? {} : null,
    };
    component.onDocumentClick({target: insideTarget} as unknown as Event);
    expect(component.showMenu()).toBe(true);
  });
});
