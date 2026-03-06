import {ComponentFixture, TestBed} from '@angular/core/testing';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {provideHttpClient} from '@angular/common/http';
import {provideRouter} from '@angular/router';

import {MarketsStocks} from './markets-stocks';

describe('MarketsStocks', () => {
  let component: MarketsStocks;
  let fixture: ComponentFixture<MarketsStocks>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsStocks],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MarketsStocks);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
