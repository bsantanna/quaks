import {TestBed} from '@angular/core/testing';
import {ThemeService} from './theme.service';

describe('ThemeService', () => {
  let service: ThemeService;

  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');

    TestBed.configureTestingModule({});
    service = TestBed.inject(ThemeService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should default to default theme', () => {
    expect(service.state().theme).toBe('default');
  });

  it('should apply data-theme attribute', () => {
    expect(document.documentElement.getAttribute('data-theme')).toBe('default');
  });

  it('should toggle to bloomnerd', () => {
    service.toggle();
    expect(service.state().theme).toBe('bloomnerd');
  });

  it('should toggle back to default', () => {
    service.toggle();
    service.toggle();
    expect(service.state().theme).toBe('default');
  });

  it('should persist to localStorage', () => {
    service.update({theme: 'bloomnerd'});
    TestBed.flushEffects();
    const stored = localStorage.getItem(ThemeService.STORAGE_KEY);
    expect(stored).toBe(JSON.stringify({theme: 'bloomnerd'}));
  });

  it('falls back to setAttribute when dataset is unavailable', () => {
    const origDataset = Object.getOwnPropertyDescriptor(document.documentElement, 'dataset');
    Object.defineProperty(document.documentElement, 'dataset', {
      value: undefined,
      configurable: true,
    });

    service.update({theme: 'matrix'});
    TestBed.flushEffects();

    expect(document.documentElement.getAttribute('data-theme')).toBe('matrix');

    if (origDataset) {
      Object.defineProperty(document.documentElement, 'dataset', origDataset);
    } else {
      delete (document.documentElement as any).dataset;
    }
  });
});
