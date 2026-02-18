import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { StockInfoHeader } from './stock-info-header';

describe('StockInfoHeader', () => {
  let component: StockInfoHeader;
  let fixture: ComponentFixture<StockInfoHeader>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockInfoHeader],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    }).compileComponents();

    fixture = TestBed.createComponent(StockInfoHeader);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('indexName', 'test-index');
    fixture.componentRef.setInput('keyTicker', 'AAPL');
    fixture.componentRef.setInput('companyName', 'Apple Inc.');
    fixture.componentRef.setInput('intervalInDates', '2024-01-01,2024-12-31');
    fixture.componentRef.setInput('useIntervalInDates', false);
    fixture.componentRef.setInput('intervalInDays', 30);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
