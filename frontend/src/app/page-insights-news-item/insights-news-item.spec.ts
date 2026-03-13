import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { InsightsNewsItem } from './insights-news-item';

describe('InsightsNewsItem', () => {
  let component: InsightsNewsItem;
  let fixture: ComponentFixture<InsightsNewsItem>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsNewsItem],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])]
    }).compileComponents();

    fixture = TestBed.createComponent(InsightsNewsItem);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
