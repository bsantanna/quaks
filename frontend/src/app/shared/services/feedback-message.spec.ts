import {TestBed} from '@angular/core/testing';
import {FeedbackMessageService} from './feedback-message.service';

describe('FeedbackMessageService', () => {
  let service: FeedbackMessageService;

  beforeEach(() => {
    jest.useFakeTimers();
    TestBed.configureTestingModule({});
    service = TestBed.inject(FeedbackMessageService);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should start with empty initial state', () => {
    const state = service.state();
    expect(state.message).toBe('');
    expect(state.type).toBe('info');
    expect(state.timeout).toBe(0);
  });

  it('should update state with new message', () => {
    service.update({message: 'Success!', type: 'success', timeout: 3000});
    expect(service.state().message).toBe('Success!');
    expect(service.state().type).toBe('success');
  });

  it('should auto-reset after 3 seconds', () => {
    service.update({message: 'Temporary', type: 'error', timeout: 3000});
    expect(service.state().message).toBe('Temporary');

    jest.advanceTimersByTime(3000);

    expect(service.state().message).toBe('');
    expect(service.state().type).toBe('info');
  });
});
