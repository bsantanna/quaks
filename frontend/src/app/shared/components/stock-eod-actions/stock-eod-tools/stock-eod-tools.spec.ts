import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { StockEodTools } from './stock-eod-tools';

describe('StockEodTools', () => {
  let component: StockEodTools;
  let fixture: ComponentFixture<StockEodTools>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockEodTools],
      providers: [provideRouter([])]
    }).compileComponents();

    fixture = TestBed.createComponent(StockEodTools);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('keyTicker', 'AAPL');
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
