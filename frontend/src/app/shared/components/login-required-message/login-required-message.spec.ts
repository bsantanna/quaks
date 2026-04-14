import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AuthService } from '../../services/auth.service';

import { LoginRequiredMessage } from './login-required-message';

describe('LoginRequiredMessage', () => {
  let component: LoginRequiredMessage;
  let fixture: ComponentFixture<LoginRequiredMessage>;
  const mockAuthService = {
    initiateLogin: jest.fn(),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoginRequiredMessage],
      providers: [
        { provide: AuthService, useValue: mockAuthService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(LoginRequiredMessage);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('notice', 'Please log in to use this feature.');
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should call initiateLogin on login click', () => {
    component.login();
    expect(mockAuthService.initiateLogin).toHaveBeenCalled();
  });
});
