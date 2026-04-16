import {routes} from './app.routes';

describe('appRoutes', () => {
  it('should define routes array', () => {
    expect(routes).toBeDefined();
    expect(routes.length).toBeGreaterThan(0);
  });

  it('should have a wildcard redirect', () => {
    const wildcard = routes.find(r => r.path === '**');
    expect(wildcard).toBeDefined();
    expect(wildcard!.redirectTo).toBe('');
  });

  it('should have market routes', () => {
    const markets = routes.find(r => r.path === 'markets');
    expect(markets).toBeDefined();
    expect(markets!.children!.length).toBeGreaterThan(0);
  });

  it('should have insights routes', () => {
    const insights = routes.find(r => r.path === 'insights');
    expect(insights).toBeDefined();
    expect(insights!.children!.length).toBeGreaterThan(0);
  });
});
