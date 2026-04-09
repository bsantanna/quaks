import {ComponentFixture, TestBed} from '@angular/core/testing';
import {SettingsDropdownComponent} from './settings-dropdown';

describe('SettingsDropdownComponent', () => {
  let component: SettingsDropdownComponent;
  let fixture: ComponentFixture<SettingsDropdownComponent>;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [SettingsDropdownComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SettingsDropdownComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should toggle menu visibility', () => {
    expect(component.showMenu()).toBe(false);
    component.toggleMenu();
    expect(component.showMenu()).toBe(true);
    component.toggleMenu();
    expect(component.showMenu()).toBe(false);
  });

  it('should select theme and close menu', () => {
    component.showMenu.set(true);
    component.selectTheme('bloomnerd');
    expect(component.themeService.state().theme).toBe('bloomnerd');
    expect(component.showMenu()).toBe(false);
  });

  it('should toggle the theme dropdown', () => {
    component.toggleThemeDropdown();
    expect(component.themeOpen()).toBe(true);

    component.toggleThemeDropdown();
    expect(component.themeOpen()).toBe(false);
  });

  it('should select a date format and close the menu', () => {
    component.showMenu.set(true);
    component.selectDateFormat('YY/MM/DD');

    expect(component.dateFormatService.state().dateFormat).toBe('YY/MM/DD');
    expect(component.showMenu()).toBe(false);
  });

  it('should close both dropdowns on outside click', () => {
    component.showMenu.set(true);
    component.themeOpen.set(true);

    component.onDocumentClick({target: document.createElement('div')} as Event);

    expect(component.showMenu()).toBe(false);
    expect(component.themeOpen()).toBe(false);
  });
});
