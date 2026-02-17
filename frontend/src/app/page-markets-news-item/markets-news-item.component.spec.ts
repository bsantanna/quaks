import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { MarketsNewsItem } from './markets-news-item.component';

describe('MarketsNewsArticle', () => {
  let component: MarketsNewsItem;
  let fixture: ComponentFixture<MarketsNewsItem>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsNewsItem],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])]
    }).compileComponents();

    fixture = TestBed.createComponent(MarketsNewsItem);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
