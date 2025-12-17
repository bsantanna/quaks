import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MarketsNewsItem } from './markets-news-item.component';

describe('MarketsNewsArticle', () => {
  let component: MarketsNewsItem;
  let fixture: ComponentFixture<MarketsNewsItem>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarketsNewsItem]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MarketsNewsItem);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
