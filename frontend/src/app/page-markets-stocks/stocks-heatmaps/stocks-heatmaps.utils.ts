import {HeatmapConstituent, MarketCapsBulkResponse, StatsCloseBulkResponse} from '../../shared';

export interface HeatmapTile {
  ticker: string;
  name: string;
  sector: string;
  industry: string;
  marketCap: number;
  percentVariance: number;
  mostRecentDate: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface SectorGroup {
  sector: string;
  tiles: HeatmapTile[];
  x: number;
  y: number;
  w: number;
  h: number;
}

export type HeatmapIndex = 'sp500' | 'nasdaq100';

interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export function getTooltipStyle(x: number, y: number, width: number, height: number): {left: number; top: number} {
  const tooltipW = 220;
  const tooltipH = 90;
  const offset = 12;

  let left = x + offset;
  let top = y - tooltipH;

  if (left + tooltipW > width) left = x - tooltipW - offset;
  if (top < 0) top = y + offset;

  return {left, top};
}

export function getTileColor(percentVariance: number): string {
  if (percentVariance === 0) return '#2a2e39';

  const intensity = Math.min(Math.abs(percentVariance) / 5, 1);
  if (percentVariance > 0) {
    const r = Math.round(20 + 10 * intensity);
    const g = Math.round(60 + 140 * intensity);
    const b = Math.round(20 + 10 * intensity);
    return `rgb(${r},${g},${b})`;
  }

  const r = Math.round(60 + 140 * intensity);
  const g = Math.round(20 + 10 * intensity);
  const b = Math.round(20 + 10 * intensity);
  return `rgb(${r},${g},${b})`;
}

export function getTileFontSize(tile: Pick<HeatmapTile, 'w' | 'h'>): number {
  const area = tile.w * tile.h;
  if (area > 15000) return 16;
  if (area > 8000) return 14;
  if (area > 3000) return 12;
  if (area > 1000) return 10;
  return 8;
}

export function shouldShowTicker(tile: Pick<HeatmapTile, 'w' | 'h'>): boolean {
  return tile.w > 30 && tile.h > 20;
}

export function shouldShowVariance(tile: Pick<HeatmapTile, 'w' | 'h'>): boolean {
  return tile.w > 40 && tile.h > 35;
}

export function getTodayIso(now: Date = new Date()): string {
  return now.toISOString().split('T')[0];
}

export function getStartDateFor(endDate: string): string {
  const date = new Date(endDate);
  date.setDate(date.getDate() - 7);
  return date.toISOString().split('T')[0];
}

export function buildHeatmapTiles(
  constituents: HeatmapConstituent[],
  stats: StatsCloseBulkResponse,
  caps: MarketCapsBulkResponse,
): {tiles: HeatmapTile[]; mostRecentDate: string} {
  const statsMap = new Map(stats.items.map(item => [item.key_ticker, item]));
  const capsMap = new Map(
    caps.items
      .filter(item => item.market_capitalization !== null)
      .map(item => [item.key_ticker, item.market_capitalization as number])
  );

  const tiles: HeatmapTile[] = constituents
    .filter(item => capsMap.has(item.ticker))
    .map(item => ({
      ticker: item.ticker,
      name: item.name,
      sector: item.sector,
      industry: item.industry,
      marketCap: capsMap.get(item.ticker) ?? 0,
      percentVariance: statsMap.get(item.ticker)?.percent_variance ?? 0,
      mostRecentDate: statsMap.get(item.ticker)?.most_recent_date ?? '',
      x: 0,
      y: 0,
      w: 0,
      h: 0,
    }));

  const dates = tiles.map(tile => tile.mostRecentDate).filter(Boolean);
  const sortedDates = [...dates].sort((a, b) => a.localeCompare(b));
  const mostRecentDate = dates.length > 0 ? sortedDates[sortedDates.length - 1] : '';

  return {tiles, mostRecentDate};
}

export function layoutHeatmapTreemap(
  tiles: HeatmapTile[],
  width: number,
  height: number,
  zoomedSector: string | null,
): SectorGroup[] {
  const w = width || 1200;
  const h = height || 700;
  const sectorMap = new Map<string, HeatmapTile[]>();

  for (const tile of tiles) {
    const sectorTiles = sectorMap.get(tile.sector) ?? [];
    sectorTiles.push(tile);
    sectorMap.set(tile.sector, sectorTiles);
  }

  let sectorItems: {sector: string; tiles: HeatmapTile[]; value: number}[];
  if (zoomedSector) {
    const zoomedTiles = sectorMap.get(zoomedSector) ?? [];
    sectorItems = [{
      sector: zoomedSector,
      tiles: zoomedTiles,
      value: zoomedTiles.reduce((sum, tile) => sum + tile.marketCap, 0),
    }];
  } else {
    sectorItems = Array.from(sectorMap.entries())
      .map(([sector, sectorTiles]) => ({
        sector,
        tiles: sectorTiles,
        value: sectorTiles.reduce((sum, tile) => sum + tile.marketCap, 0),
      }))
      .sort((a, b) => b.value - a.value);
  }

  const totalValue = sectorItems.reduce((sum, item) => sum + item.value, 0);
  const sectorRects = squarify(
    sectorItems.map(item => totalValue === 0 ? 0 : item.value / totalValue),
    {x: 0, y: 0, w, h},
  );

  return sectorItems.map((item, index) => {
    const rect = sectorRects[index];
    const padding = 22;
    const innerRect = {
      x: rect.x + 2,
      y: rect.y + padding,
      w: Math.max(rect.w - 4, 0),
      h: Math.max(rect.h - padding - 2, 0),
    };
    const sectorTotal = item.tiles.reduce((sum, tile) => sum + tile.marketCap, 0);
    const tileRects = squarify(
      [...item.tiles]
        .sort((a, b) => b.marketCap - a.marketCap)
        .map(tile => sectorTotal === 0 ? 0 : tile.marketCap / sectorTotal),
      innerRect,
    );

    const sortedTiles = [...item.tiles].sort((a, b) => b.marketCap - a.marketCap);
    for (let tileIndex = 0; tileIndex < sortedTiles.length; tileIndex++) {
      const tileRect = tileRects[tileIndex];
      sortedTiles[tileIndex].x = tileRect.x;
      sortedTiles[tileIndex].y = tileRect.y;
      sortedTiles[tileIndex].w = tileRect.w;
      sortedTiles[tileIndex].h = tileRect.h;
    }

    return {
      sector: item.sector,
      tiles: sortedTiles,
      x: rect.x,
      y: rect.y,
      w: rect.w,
      h: rect.h,
    };
  });
}

export function squarify(values: number[], rect: Rect): Rect[] {
  if (values.length === 0) return [];
  if (values.length === 1) return [rect];

  const results: Rect[] = new Array(values.length);
  const indices = values.map((_, index) => index).sort((a, b) => values[b] - values[a]);
  const sorted = indices.map(index => values[index]);

  squarifyRecursive(sorted, indices, rect, results);
  return results;
}

function squarifyRecursive(values: number[], indices: number[], rect: Rect, results: Rect[]): void {
  if (values.length === 0) return;
  if (values.length === 1) {
    results[indices[0]] = {...rect};
    return;
  }

  const total = values.reduce((sum, value) => sum + value, 0);
  if (total === 0) {
    for (const index of indices) {
      results[index] = {x: rect.x, y: rect.y, w: 0, h: 0};
    }
    return;
  }

  const horizontal = rect.w >= rect.h;
  const side = horizontal ? rect.h : rect.w;
  let rowValues = [values[0]];
  let rowIndices = [indices[0]];
  let rowSum = values[0];
  let bestAspect = worstAspect(rowValues, rowSum, total, side);

  for (let i = 1; i < values.length; i++) {
    const testValues = [...rowValues, values[i]];
    const testSum = rowSum + values[i];
    const testAspect = worstAspect(testValues, testSum, total, side);

    if (testAspect <= bestAspect) {
      rowValues = testValues;
      rowIndices = [...rowIndices, indices[i]];
      rowSum = testSum;
      bestAspect = testAspect;
    } else {
      break;
    }
  }

  const rowFraction = rowSum / total;
  const rowSize = horizontal ? rect.w * rowFraction : rect.h * rowFraction;
  let offset = 0;

  for (let i = 0; i < rowValues.length; i++) {
    const tileFraction = rowValues[i] / rowSum;
    const tileSize = side * tileFraction;
    const gap = 1;

    results[rowIndices[i]] = horizontal
      ? {
          x: rect.x + gap / 2,
          y: rect.y + offset + gap / 2,
          w: Math.max(rowSize - gap, 0),
          h: Math.max(tileSize - gap, 0),
        }
      : {
          x: rect.x + offset + gap / 2,
          y: rect.y + gap / 2,
          w: Math.max(tileSize - gap, 0),
          h: Math.max(rowSize - gap, 0),
        };

    offset += tileSize;
  }

  const remainingValues = values.slice(rowValues.length);
  const remainingIndices = indices.slice(rowValues.length);
  const nextRect = horizontal
    ? {x: rect.x + rowSize, y: rect.y, w: rect.w - rowSize, h: rect.h}
    : {x: rect.x, y: rect.y + rowSize, w: rect.w, h: rect.h - rowSize};

  squarifyRecursive(remainingValues, remainingIndices, nextRect, results);
}

export function worstAspect(values: number[], rowSum: number, total: number, side: number): number {
  if (side === 0 || total === 0 || rowSum === 0) return Infinity;

  const rowArea = (rowSum / total) * side * side;
  let worst = 0;

  for (const value of values) {
    const tileArea = (value / rowSum) * rowArea;
    const tileWidth = rowArea / side;
    const tileHeight = tileArea / tileWidth;
    const aspect = Math.max(tileWidth / tileHeight, tileHeight / tileWidth);
    if (aspect > worst) worst = aspect;
  }

  return worst;
}
