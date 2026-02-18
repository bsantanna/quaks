import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { MarketsNewsRelated } from './markets-news-related';

describe('MarketsNewsRelated', () => {
  let component: MarketsNewsRelated;
  let fixture: ComponentFixture<MarketsNewsRelated>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsNewsRelated],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])]
    }).compileComponents();

    fixture = TestBed.createComponent(MarketsNewsRelated);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
