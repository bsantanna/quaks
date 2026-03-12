import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SmallScreenMessage } from './small-screen-message';

describe('SmallScreenMessage', () => {
  let component: SmallScreenMessage;
  let fixture: ComponentFixture<SmallScreenMessage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SmallScreenMessage]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SmallScreenMessage);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('notice', 'Test notice message');
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
