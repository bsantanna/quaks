import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StockEodActions } from './stock-eod-actions';

describe('StockEodActions', () => {
  let component: StockEodActions;
  let fixture: ComponentFixture<StockEodActions>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockEodActions]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StockEodActions);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
