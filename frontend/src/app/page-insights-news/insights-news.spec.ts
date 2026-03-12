import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';

import { InsightsNews } from './insights-news';

describe('InsightsNews', () => {
  let component: InsightsNews;
  let fixture: ComponentFixture<InsightsNews>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsNews],
      providers: [provideHttpClient()]
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
