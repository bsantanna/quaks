import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StocksHeatmaps } from './stocks-heatmaps';

describe('StocksHeatmaps', () => {
  let component: StocksHeatmaps;
  let fixture: ComponentFixture<StocksHeatmaps>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StocksHeatmaps]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StocksHeatmaps);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
