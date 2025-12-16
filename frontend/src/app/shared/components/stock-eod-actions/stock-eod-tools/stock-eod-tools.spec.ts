import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StockEodTools } from './stock-eod-tools';

describe('StockEodTools', () => {
  let component: StockEodTools;
  let fixture: ComponentFixture<StockEodTools>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockEodTools]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StockEodTools);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
