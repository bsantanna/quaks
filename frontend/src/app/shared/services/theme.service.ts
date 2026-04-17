import {effect, inject, Injectable, PLATFORM_ID, signal, WritableSignal} from '@angular/core';
import {isPlatformBrowser, DOCUMENT} from '@angular/common';
import {SharedStateService, ThemePreference, ThemeName} from '../models/navigation.models';

@Injectable({
  providedIn: 'root',
})
export class ThemeService implements SharedStateService<ThemePreference> {

  static readonly STORAGE_KEY = 'ThemePreference';
  static readonly DEFAULT_THEME: ThemeName = 'default';

  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly document = inject(DOCUMENT);
  readonly state!: WritableSignal<ThemePreference>;

  constructor() {
    const stored = this.isBrowser
      ? localStorage.getItem(ThemeService.STORAGE_KEY)
      : null;

    this.state = signal<ThemePreference>(
      stored ? JSON.parse(stored) : {theme: ThemeService.DEFAULT_THEME}
    );

    this.applyTheme(this.state().theme);

    effect(() => {
      const pref = this.state();
      this.applyTheme(pref.theme);
      if (this.isBrowser) {
        localStorage.setItem(ThemeService.STORAGE_KEY, JSON.stringify(pref));
      }
    });
  }

  update(pref: ThemePreference): void {
    this.state.set(pref);
  }

  toggle(): void {
    const current = this.state().theme;
    this.update({theme: current === 'default' ? 'bloomnerd' : 'default'});
  }

  private applyTheme(theme: ThemeName): void {
    const el = this.document.documentElement;
    if (el.dataset) {
      el.dataset['theme'] = theme;
    }
  }
}
