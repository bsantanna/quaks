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
});
