import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MarketsPerformanceComparison } from './markets-performance-comparison';

describe('MarketsPerformanceComparison', () => {
  let component: MarketsPerformanceComparison;
  let fixture: ComponentFixture<MarketsPerformanceComparison>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsPerformanceComparison]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MarketsPerformanceComparison);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
