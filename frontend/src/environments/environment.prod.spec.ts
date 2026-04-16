import {environment} from './environment.prod';

describe('environment.prod', () => {
  it('should be marked as production', () => {
    expect(environment.production).toBe(true);
  });

  it('should have required config keys', () => {
    expect(environment.apiBaseUrl).toBeTruthy();
    expect(environment.keycloakUrl).toBeTruthy();
    expect(environment.keycloakRealm).toBeTruthy();
    expect(environment.keycloakClientId).toBeTruthy();
  });
});
