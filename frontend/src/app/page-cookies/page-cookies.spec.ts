import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PageCookies } from './page-cookies';

describe('PageCookies', () => {
  let component: PageCookies;
  let fixture: ComponentFixture<PageCookies>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PageCookies]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PageCookies);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
