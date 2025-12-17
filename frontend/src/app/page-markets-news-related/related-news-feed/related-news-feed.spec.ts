import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RelatedNewsFeed } from './related-news-feed';

describe('RelatedNewsFeed', () => {
  let component: RelatedNewsFeed;
  let fixture: ComponentFixture<RelatedNewsFeed>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RelatedNewsFeed]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RelatedNewsFeed);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
