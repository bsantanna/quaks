import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { StockEodActions } from './stock-eod-actions';

describe('StockEodActions', () => {
  let component: StockEodActions;
  let fixture: ComponentFixture<StockEodActions>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockEodActions],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    }).compileComponents();

    fixture = TestBed.createComponent(StockEodActions);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('keyTicker', 'AAPL');
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
