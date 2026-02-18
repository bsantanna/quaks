import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MarketsNews } from './markets-news';

describe('MarketsNews', () => {
  let component: MarketsNews;
  let fixture: ComponentFixture<MarketsNews>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsNews]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MarketsNews);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
