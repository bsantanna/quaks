import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NewsFeed } from './news-feed.component';

describe('NewsFeed', () => {
  let component: NewsFeed;
  let fixture: ComponentFixture<NewsFeed>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NewsFeed]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NewsFeed);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
