import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { InsightsPreview } from './insights-preview';

describe('InsightsPreview', () => {
  let component: InsightsPreview;
  let fixture: ComponentFixture<InsightsPreview>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsPreview],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])]
    }).compileComponents();

    fixture = TestBed.createComponent(InsightsPreview);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
