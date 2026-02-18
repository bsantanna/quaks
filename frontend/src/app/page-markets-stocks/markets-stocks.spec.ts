import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MarketsStocks } from './markets-stocks';

describe('MarketsStocks', () => {
  let component: MarketsStocks;
  let fixture: ComponentFixture<MarketsStocks>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsStocks]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MarketsStocks);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
