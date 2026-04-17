describe('main.ts', () => {
  it('should export the bootstrap module', async () => {
    // Verify the module can be imported without throwing
    const main = await import('./main');
    expect(main).toBeDefined();
  });
});
