import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StockComparisonAutocomplete } from './stock-comparison-autocomplete';

describe('StockComparisonAutocomplete', () => {
  let component: StockComparisonAutocomplete;
  let fixture: ComponentFixture<StockComparisonAutocomplete>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockComparisonAutocomplete]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StockComparisonAutocomplete);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
