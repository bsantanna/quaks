import {ComponentFixture, TestBed} from '@angular/core/testing';
import {ActivatedRoute, convertToParamMap} from '@angular/router';
import {BehaviorSubject} from 'rxjs';

import {InsightsQuaksStocksExpert} from './insights-quaks-stocks-expert';

describe('InsightsQuaksStocksExpert', () => {
  let component: InsightsQuaksStocksExpert;
  let fixture: ComponentFixture<InsightsQuaksStocksExpert>;
  let paramMap$: BehaviorSubject<any>;

  beforeEach(async () => {
    paramMap$ = new BehaviorSubject(convertToParamMap({keyTicker: 'AAPL'}));

    await TestBed.configureTestingModule({
      imports: [InsightsQuaksStocksExpert],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: paramMap$.asObservable(),
            snapshot: {paramMap: convertToParamMap({keyTicker: 'AAPL'})},
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(InsightsQuaksStocksExpert);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
