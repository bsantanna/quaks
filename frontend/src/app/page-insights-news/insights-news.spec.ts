import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InsightsNews } from './insights-news';

describe('InsightsNews', () => {
  let component: InsightsNews;
  let fixture: ComponentFixture<InsightsNews>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsNews]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InsightsNews);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
