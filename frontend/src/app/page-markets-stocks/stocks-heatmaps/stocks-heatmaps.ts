import {Component, computed, ElementRef, inject, OnDestroy, PLATFORM_ID, signal, viewChild} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {HttpClient} from '@angular/common/http';
import {forkJoin} from 'rxjs';
import {Router} from '@angular/router';
import {HeatmapConstituent, StatsClose} from '../../shared';
import {MarketsStatsService} from '../../shared';

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

type HeatmapIndex = 'sp500' | 'nasdaq100';

@Component({
  selector: 'app-stocks-heatmaps',
  imports: [],
  templateUrl: './stocks-heatmaps.html',
  styleUrl: './stocks-heatmaps.scss',
})
export class StocksHeatmaps implements OnDestroy {
  private readonly platformId = inject(PLATFORM_ID);
  private readonly httpClient = inject(HttpClient);
  private readonly statsService = inject(MarketsStatsService);
  private readonly router = inject(Router);
  private readonly containerRef = viewChild<ElementRef>('heatmapContainer');

  readonly selectedIndex = signal<HeatmapIndex>('sp500');
  readonly loading = signal(true);
  readonly sectorGroups = signal<SectorGroup[]>([]);
  readonly zoomedSector = signal<string | null>(null);
  readonly hoveredTile = signal<HeatmapTile | null>(null);
  readonly mouseX = signal(0);
  readonly mouseY = signal(0);

  readonly tooltipStyle = computed(() => {
    const x = this.mouseX();
    const y = this.mouseY();
    const w = this.containerWidth || 1200;
    const h = this.containerHeight || 700;
    const tooltipW = 220;
    const tooltipH = 90;
    const offset = 12;

    let left = x + offset;
    let top = y - tooltipH;

    if (left + tooltipW > w) left = x - tooltipW - offset;
    if (top < 0) top = y + offset;

    return {left, top};
  });

  readonly visibleGroups = computed(() => {
    const zoomed = this.zoomedSector();
    const groups = this.sectorGroups();
    if (!zoomed) return groups;
    return groups.filter(g => g.sector === zoomed);
  });

  private allTiles: HeatmapTile[] = [];
  private resizeObserver: ResizeObserver | null = null;
  private containerWidth = 0;
  private containerHeight = 0;

  constructor() {
    if (isPlatformBrowser(this.platformId)) {
      this.loadData();
      this.setupResize();
    }
  }

  ngOnDestroy() {
    this.resizeObserver?.disconnect();
  }

  switchIndex(index: HeatmapIndex) {
    this.selectedIndex.set(index);
    this.zoomedSector.set(null);
    this.loadData();
  }

  toggleZoom(sector: string) {
    this.zoomedSector.set(this.zoomedSector() === sector ? null : sector);
    this.relayout();
  }

  zoomOut() {
    this.zoomedSector.set(null);
    this.relayout();
  }

  onMouseMove(event: MouseEvent) {
    const container = this.containerRef()?.nativeElement;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    this.mouseX.set(event.clientX - rect.left);
    this.mouseY.set(event.clientY - rect.top);
  }

  navigateToStock(ticker: string) {
    this.router.navigate(['/markets/stocks', ticker]);
  }

  tileColor(pv: number): string {
    if (pv === 0) return '#2a2e39';
    const intensity = Math.min(Math.abs(pv) / 5, 1);
    if (pv > 0) {
      const r = Math.round(20 + 10 * intensity);
      const g = Math.round(60 + 140 * intensity);
      const b = Math.round(20 + 10 * intensity);
      return `rgb(${r},${g},${b})`;
    } else {
      const r = Math.round(60 + 140 * intensity);
      const g = Math.round(20 + 10 * intensity);
      const b = Math.round(20 + 10 * intensity);
      return `rgb(${r},${g},${b})`;
    }
  }

  tileFontSize(tile: HeatmapTile): number {
    const area = tile.w * tile.h;
    if (area > 15000) return 16;
    if (area > 8000) return 14;
    if (area > 3000) return 12;
    if (area > 1000) return 10;
    return 8;
  }

  showTicker(tile: HeatmapTile): boolean {
    return tile.w > 30 && tile.h > 20;
  }

  showVariance(tile: HeatmapTile): boolean {
    return tile.w > 40 && tile.h > 35;
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '';
    const [y, m, d] = dateStr.split('-');
    return `${d}/${m}/${y.slice(2)}`;
  }

  private setupResize() {
    if (typeof ResizeObserver === 'undefined') return;

    this.resizeObserver = new ResizeObserver(() => {
      const el = this.containerRef()?.nativeElement;
      if (el) {
        this.containerWidth = el.clientWidth;
        this.containerHeight = el.clientHeight;
        this.relayout();
      }
    });

    setTimeout(() => {
      const el = this.containerRef()?.nativeElement;
      if (el) {
        this.containerWidth = el.clientWidth;
        this.containerHeight = el.clientHeight;
        this.resizeObserver!.observe(el);
      }
    });
  }

  private loadData() {
    this.loading.set(true);
    const jsonFile = this.selectedIndex() === 'sp500'
      ? '/json/heatmap_sp500.json'
      : '/json/heatmap_nasdaq100.json';

    this.httpClient.get<HeatmapConstituent[]>(jsonFile).subscribe(constituents => {
      const tickers = constituents.map(c => c.ticker);

      forkJoin({
        stats: this.statsService.getStatsCloseBulk('quaks_stocks-eod_latest', tickers),
        caps: this.statsService.getMarketCapsBulk('quaks_stocks-metadata_latest', tickers),
      }).subscribe(({stats, caps}) => {
        const statsMap = new Map<string, StatsClose>();
        for (const s of stats.items) statsMap.set(s.key_ticker, s);

        const capsMap = new Map<string, number>();
        for (const c of caps.items) {
          if (c.market_capitalization) capsMap.set(c.key_ticker, c.market_capitalization);
        }

        const tiles: HeatmapTile[] = constituents
          .filter(c => capsMap.has(c.ticker))
          .map(c => ({
            ticker: c.ticker,
            name: c.name,
            sector: c.sector,
            industry: c.industry,
            marketCap: capsMap.get(c.ticker) || 0,
            percentVariance: statsMap.get(c.ticker)?.percent_variance ?? 0,
            mostRecentDate: statsMap.get(c.ticker)?.most_recent_date ?? '',
            x: 0, y: 0, w: 0, h: 0,
          }));

        this.allTiles = tiles;
        this.layoutTreemap(tiles);
        this.loading.set(false);
      });
    });
  }

  private relayout() {
    if (this.allTiles.length > 0) {
      this.layoutTreemap(this.allTiles);
    }
  }

  private layoutTreemap(tiles: HeatmapTile[]) {
    const w = this.containerWidth || 1200;
    const h = this.containerHeight || 700;
    const zoomed = this.zoomedSector();

    const sectorMap = new Map<string, HeatmapTile[]>();
    for (const t of tiles) {
      const list = sectorMap.get(t.sector) || [];
      list.push(t);
      sectorMap.set(t.sector, list);
    }

    let sectorItems: {sector: string; tiles: HeatmapTile[]; value: number}[];

    if (zoomed) {
      const zoomedTiles = sectorMap.get(zoomed) || [];
      sectorItems = [{sector: zoomed, tiles: zoomedTiles, value: zoomedTiles.reduce((s, t) => s + t.marketCap, 0)}];
    } else {
      sectorItems = Array.from(sectorMap.entries())
        .map(([sector, sectorTiles]) => ({
          sector,
          tiles: sectorTiles,
          value: sectorTiles.reduce((s, t) => s + t.marketCap, 0),
        }))
        .sort((a, b) => b.value - a.value);
    }

    const totalValue = sectorItems.reduce((s, si) => s + si.value, 0);
    const sectorRects = this.squarify(
      sectorItems.map(si => si.value / totalValue),
      {x: 0, y: 0, w, h}
    );

    const groups: SectorGroup[] = [];
    for (let i = 0; i < sectorItems.length; i++) {
      const si = sectorItems[i];
      const rect = sectorRects[i];
      const padding = 22;
      const innerRect = {
        x: rect.x + 2,
        y: rect.y + padding,
        w: Math.max(rect.w - 4, 0),
        h: Math.max(rect.h - padding - 2, 0),
      };

      const sectorTotal = si.tiles.reduce((s, t) => s + t.marketCap, 0);
      const tileRects = this.squarify(
        si.tiles.sort((a, b) => b.marketCap - a.marketCap).map(t => t.marketCap / sectorTotal),
        innerRect
      );

      for (let j = 0; j < si.tiles.length; j++) {
        const tr = tileRects[j];
        si.tiles[j].x = tr.x;
        si.tiles[j].y = tr.y;
        si.tiles[j].w = tr.w;
        si.tiles[j].h = tr.h;
      }

      groups.push({
        sector: si.sector,
        tiles: si.tiles,
        x: rect.x,
        y: rect.y,
        w: rect.w,
        h: rect.h,
      });
    }

    this.sectorGroups.set(groups);
  }

  private squarify(
    values: number[],
    rect: {x: number; y: number; w: number; h: number}
  ): {x: number; y: number; w: number; h: number}[] {
    if (values.length === 0) return [];
    if (values.length === 1) return [rect];

    const results: {x: number; y: number; w: number; h: number}[] = new Array(values.length);
    const indices = values.map((v, i) => i).sort((a, b) => values[b] - values[a]);
    const sorted = indices.map(i => values[i]);

    this.squarifyRecursive(sorted, indices, rect, results);
    return results;
  }

  private squarifyRecursive(
    values: number[],
    indices: number[],
    rect: {x: number; y: number; w: number; h: number},
    results: {x: number; y: number; w: number; h: number}[]
  ) {
    if (values.length === 0) return;
    if (values.length === 1) {
      results[indices[0]] = {...rect};
      return;
    }

    const total = values.reduce((s, v) => s + v, 0);
    if (total === 0) {
      for (let i = 0; i < values.length; i++) {
        results[indices[i]] = {x: rect.x, y: rect.y, w: 0, h: 0};
      }
      return;
    }

    const horizontal = rect.w >= rect.h;
    const side = horizontal ? rect.h : rect.w;

    let rowValues: number[] = [values[0]];
    let rowIndices: number[] = [indices[0]];
    let rowSum = values[0];
    let bestAspect = this.worstAspect(rowValues, rowSum, total, side);

    for (let i = 1; i < values.length; i++) {
      const testValues = [...rowValues, values[i]];
      const testSum = rowSum + values[i];
      const testAspect = this.worstAspect(testValues, testSum, total, side);

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

      if (horizontal) {
        results[rowIndices[i]] = {
          x: rect.x + gap / 2,
          y: rect.y + offset + gap / 2,
          w: Math.max(rowSize - gap, 0),
          h: Math.max(tileSize - gap, 0),
        };
      } else {
        results[rowIndices[i]] = {
          x: rect.x + offset + gap / 2,
          y: rect.y + gap / 2,
          w: Math.max(tileSize - gap, 0),
          h: Math.max(rowSize - gap, 0),
        };
      }
      offset += tileSize;
    }

    const remaining = values.slice(rowValues.length);
    const remainingIndices = indices.slice(rowValues.length);
    const newRect = horizontal
      ? {x: rect.x + rowSize, y: rect.y, w: rect.w - rowSize, h: rect.h}
      : {x: rect.x, y: rect.y + rowSize, w: rect.w, h: rect.h - rowSize};

    this.squarifyRecursive(remaining, remainingIndices, newRect, results);
  }

  private worstAspect(values: number[], rowSum: number, total: number, side: number): number {
    if (side === 0 || total === 0 || rowSum === 0) return Infinity;
    const rowArea = (rowSum / total) * side * side;
    let worst = 0;
    for (const v of values) {
      const tileArea = (v / rowSum) * rowArea;
      const tileWidth = rowArea / side;
      const tileHeight = tileArea / tileWidth;
      const aspect = Math.max(tileWidth / tileHeight, tileHeight / tileWidth);
      if (aspect > worst) worst = aspect;
    }
    return worst;
  }
}
