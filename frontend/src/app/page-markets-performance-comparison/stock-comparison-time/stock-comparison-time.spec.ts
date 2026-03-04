import {ComponentFixture, TestBed} from '@angular/core/testing';
import {StockComparisonTime} from './stock-comparison-time';

describe('StockComparisonTime', () => {
  let component: StockComparisonTime;
  let fixture: ComponentFixture<StockComparisonTime>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockComparisonTime],
    }).compileComponents();

    fixture = TestBed.createComponent(StockComparisonTime);
    fixture.componentRef.setInput('intervalInDays', 365);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have 4 range options', () => {
    expect(component.ranges).toEqual([
      {label: '3M', days: 90},
      {label: '6M', days: 180},
      {label: '9M', days: 270},
      {label: '1Y', days: 365},
    ]);
  });

  it('should emit intervalInDaysChange on setInterval', () => {
    const spy = jest.fn();
    component.intervalInDaysChange.subscribe(spy);
    component.setInterval(90);
    expect(spy).toHaveBeenCalledWith(90);
  });

  it('should emit different values for each range', () => {
    const spy = jest.fn();
    component.intervalInDaysChange.subscribe(spy);
    component.setInterval(180);
    expect(spy).toHaveBeenCalledWith(180);
    component.setInterval(270);
    expect(spy).toHaveBeenCalledWith(270);
  });
});
