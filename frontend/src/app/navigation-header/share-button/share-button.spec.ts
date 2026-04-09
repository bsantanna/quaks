import { ComponentFixture, TestBed } from '@angular/core/testing';
import {signal} from '@angular/core';
import { ShareButtonComponent } from './share-button';
import {FeedbackMessageService, ShareUrlService} from '../../shared';

describe('ShareButton', () => {
  let component: ShareButtonComponent;
  let fixture: ComponentFixture<ShareButtonComponent>;
  const feedbackMessageService = {
    update: jest.fn(),
  };
  const shareUrlService = {
    state: signal({url: 'https://quaks.ai/insights', title: 'Quaks Insight'}),
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    Object.defineProperty(navigator, 'clipboard', {
      value: {writeText: jest.fn()},
      configurable: true,
    });

    await TestBed.configureTestingModule({
      imports: [ShareButtonComponent],
      providers: [
        {provide: FeedbackMessageService, useValue: feedbackMessageService},
        {provide: ShareUrlService, useValue: shareUrlService},
      ],
    })
    .compileComponents();

    fixture = TestBed.createComponent(ShareButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('toggles the menu', () => {
    component.toggleMenu();
    expect(component.showMenu()).toBe(true);

    component.toggleMenu();
    expect(component.showMenu()).toBe(false);
  });

  it('opens social share targets in a new tab', () => {
    const openSpy = jest.spyOn(window, 'open').mockImplementation(() => null);
    component.showMenu.set(true);

    component.share('facebook');

    expect(component.showMenu()).toBe(false);
    expect(openSpy).toHaveBeenCalledWith(
      'https://www.facebook.com/sharer.php?u=https%3A%2F%2Fquaks.ai%2Finsights',
      '_blank',
    );
  });

  it('copies the current url and shows feedback', () => {
    component.share('copy');

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('https://quaks.ai/insights');
    expect(feedbackMessageService.update).toHaveBeenCalledWith({
      message: 'Link copied',
      type: 'info',
      timeout: 3000,
    });
  });

  it('closes the menu on outside clicks', () => {
    component.showMenu.set(true);
    component.onDocumentClick({target: document.createElement('div')} as Event);
    expect(component.showMenu()).toBe(false);

    component.showMenu.set(true);
    const insideTarget = document.createElement('button');
    const host = document.createElement('app-share-button');
    host.appendChild(insideTarget);
    component.onDocumentClick({target: insideTarget} as Event);
    expect(component.showMenu()).toBe(true);
  });
});
