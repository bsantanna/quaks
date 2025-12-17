import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NewsMediaCards } from './news-media-cards';

describe('NewsMediaCards', () => {
  let component: NewsMediaCards;
  let fixture: ComponentFixture<NewsMediaCards>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NewsMediaCards]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NewsMediaCards);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
