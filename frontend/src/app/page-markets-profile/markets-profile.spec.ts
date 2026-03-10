import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { MarketsProfile } from './markets-profile';

describe('MarketsProfile', () => {
  let component: MarketsProfile;
  let fixture: ComponentFixture<MarketsProfile>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsProfile],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MarketsProfile);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should format large numbers', () => {
    expect(component.formatLargeNumber(1_500_000_000_000)).toBe('1.50T');
    expect(component.formatLargeNumber(2_300_000_000)).toBe('2.30B');
    expect(component.formatLargeNumber(45_000_000)).toBe('45.00M');
    expect(component.formatLargeNumber(1_500)).toBe('1.5K');
    expect(component.formatLargeNumber(null)).toBe('--');
  });

  it('should format percentages', () => {
    expect(component.formatPercent(0.2534)).toBe('25.34%');
    expect(component.formatPercent(-0.05)).toBe('-5.00%');
    expect(component.formatPercent(null)).toBe('--');
  });

  it('should format dates', () => {
    expect(component.formatDate('2025-03-15')).toBe('15/03/25');
    expect(component.formatDate(null)).toBe('--');
  });
});
