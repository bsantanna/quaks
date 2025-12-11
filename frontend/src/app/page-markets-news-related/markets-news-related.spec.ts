import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MarketsNewsRelated } from './markets-news-related';

describe('MarketsNewsRelated', () => {
  let component: MarketsNewsRelated;
  let fixture: ComponentFixture<MarketsNewsRelated>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsNewsRelated]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MarketsNewsRelated);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
