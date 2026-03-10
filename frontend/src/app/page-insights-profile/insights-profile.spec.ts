import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InsightsProfile } from './insights-profile';

describe('InsightsProfile', () => {
  let component: InsightsProfile;
  let fixture: ComponentFixture<InsightsProfile>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsProfile]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InsightsProfile);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
