import {appConfig} from './app.config';

describe('appConfig', () => {
  it('should have providers array', () => {
    expect(appConfig.providers).toBeDefined();
    expect(appConfig.providers.length).toBeGreaterThan(0);
  });
});
