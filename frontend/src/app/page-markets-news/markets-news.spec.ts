import {ComponentFixture, TestBed} from '@angular/core/testing';
import {ActivatedRoute} from '@angular/router';
import {BehaviorSubject} from 'rxjs';

import {MarketsNews} from './markets-news';

describe('MarketsNews', () => {
  let component: MarketsNews;
  let fixture: ComponentFixture<MarketsNews>;
  let queryParams$: BehaviorSubject<Record<string, string>>;

  beforeEach(async () => {
    queryParams$ = new BehaviorSubject<Record<string, string>>({});

    await TestBed.configureTestingModule({
      imports: [MarketsNews],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: {queryParams: queryParams$.asObservable()},
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MarketsNews);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have empty searchTerm by default', () => {
    expect(component.searchTerm()).toBe('');
  });

  it('should read search_term from query params', () => {
    queryParams$.next({search_term: 'Tesla'});
    fixture.detectChanges();
    expect(component.searchTerm()).toBe('Tesla');
  });

  it('should update searchTerm when query params change', () => {
    queryParams$.next({search_term: 'Apple'});
    fixture.detectChanges();
    expect(component.searchTerm()).toBe('Apple');

    queryParams$.next({search_term: 'Microsoft'});
    fixture.detectChanges();
    expect(component.searchTerm()).toBe('Microsoft');
  });

  it('should return empty string when search_term is removed from query params', () => {
    queryParams$.next({search_term: 'Tesla'});
    fixture.detectChanges();
    expect(component.searchTerm()).toBe('Tesla');

    queryParams$.next({});
    fixture.detectChanges();
    expect(component.searchTerm()).toBe('');
  });
});
