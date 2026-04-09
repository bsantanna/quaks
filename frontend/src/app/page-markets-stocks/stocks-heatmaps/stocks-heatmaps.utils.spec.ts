import {
  buildHeatmapTiles,
  getStartDateFor,
  getTileColor,
  getTileFontSize,
  getTodayIso,
  getTooltipStyle,
  layoutHeatmapTreemap,
  shouldShowTicker,
  shouldShowVariance,
  squarify,
  worstAspect,
} from './stocks-heatmaps.utils';

describe('stocks-heatmaps utils', () => {
  it('calculates tooltip placement near edges', () => {
    expect(getTooltipStyle(100, 100, 1200, 700)).toEqual({left: 112, top: 10});
    expect(getTooltipStyle(1190, 20, 1200, 700)).toEqual({left: 958, top: 32});
  });

  it('returns expected colors and visibility thresholds', () => {
    expect(getTileColor(0)).toBe('#2a2e39');
    expect(getTileColor(4)).toMatch(/^rgb\(\d+,\d+,\d+\)$/);
    expect(getTileColor(-4)).toMatch(/^rgb\(\d+,\d+,\d+\)$/);
    expect(getTileFontSize({w: 10, h: 10})).toBe(8);
    expect(getTileFontSize({w: 40, h: 30})).toBe(10);
    expect(getTileFontSize({w: 70, h: 50})).toBe(12);
    expect(shouldShowTicker({w: 31, h: 21})).toBe(true);
    expect(shouldShowTicker({w: 30, h: 21})).toBe(false);
    expect(shouldShowVariance({w: 41, h: 36})).toBe(true);
    expect(shouldShowVariance({w: 41, h: 35})).toBe(false);
  });

  it('builds dates from a stable input', () => {
    expect(getTodayIso(new Date('2026-04-09T12:00:00Z'))).toBe('2026-04-09');
    expect(getStartDateFor('2026-04-09')).toBe('2026-04-02');
  });

  it('builds tiles from constituents and response payloads', () => {
    const result = buildHeatmapTiles(
      [
        {ticker: 'AAPL', name: 'Apple', sector: 'Tech', industry: 'Hardware'},
        {ticker: 'MSFT', name: 'Microsoft', sector: 'Tech', industry: 'Software'},
        {ticker: 'XOM', name: 'Exxon', sector: 'Energy', industry: 'Oil'},
      ],
      {
        items: [
          {
            key_ticker: 'AAPL',
            most_recent_close: 10,
            most_recent_date: '2026-04-08',
            most_recent_low: 9,
            most_recent_high: 11,
            most_recent_volume: 100,
            most_recent_open: 10,
            percent_variance: 2,
          },
          {
            key_ticker: 'MSFT',
            most_recent_close: 20,
            most_recent_date: '2026-04-09',
            most_recent_low: 19,
            most_recent_high: 21,
            most_recent_volume: 200,
            most_recent_open: 20,
            percent_variance: -1,
          },
        ],
      },
      {
        items: [
          {key_ticker: 'AAPL', market_capitalization: 100},
          {key_ticker: 'MSFT', market_capitalization: 80},
          {key_ticker: 'XOM', market_capitalization: null},
        ],
      },
    );

    expect(result.tiles).toHaveLength(2);
    expect(result.tiles[0].ticker).toBe('AAPL');
    expect(result.tiles[1].percentVariance).toBe(-1);
    expect(result.mostRecentDate).toBe('2026-04-09');
  });

  it('lays out treemap groups and supports zooming', () => {
    const tiles = [
      {ticker: 'AAPL', name: 'Apple', sector: 'Tech', industry: 'Hardware', marketCap: 100, percentVariance: 1, mostRecentDate: '2026-04-09', x: 0, y: 0, w: 0, h: 0},
      {ticker: 'MSFT', name: 'Microsoft', sector: 'Tech', industry: 'Software', marketCap: 80, percentVariance: 2, mostRecentDate: '2026-04-09', x: 0, y: 0, w: 0, h: 0},
      {ticker: 'XOM', name: 'Exxon', sector: 'Energy', industry: 'Oil', marketCap: 60, percentVariance: -1, mostRecentDate: '2026-04-09', x: 0, y: 0, w: 0, h: 0},
    ];

    const groups = layoutHeatmapTreemap(tiles, 1200, 700, null);
    expect(groups).toHaveLength(2);
    expect(groups[0].tiles.every(tile => tile.w >= 0 && tile.h >= 0)).toBe(true);

    const zoomedGroups = layoutHeatmapTreemap(tiles, 1200, 700, 'Tech');
    expect(zoomedGroups).toHaveLength(1);
    expect(zoomedGroups[0].sector).toBe('Tech');
  });

  it('handles degenerate squarify inputs', () => {
    expect(squarify([], {x: 0, y: 0, w: 100, h: 100})).toEqual([]);
    expect(squarify([1], {x: 0, y: 0, w: 100, h: 100})).toEqual([{x: 0, y: 0, w: 100, h: 100}]);
    expect(squarify([0, 0], {x: 0, y: 0, w: 100, h: 100})).toEqual([
      {x: 0, y: 0, w: 0, h: 0},
      {x: 0, y: 0, w: 0, h: 0},
    ]);
    expect(worstAspect([1], 1, 1, 0)).toBe(Infinity);
  });
});
