import {Component, computed, ElementRef, inject, OnDestroy, PLATFORM_ID, signal, viewChild} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {HttpClient} from '@angular/common/http';
import {forkJoin} from 'rxjs';
import {ActivatedRoute, Router} from '@angular/router';
import {HeatmapConstituent} from '../../shared';
import {MarketsStatsService, DateFormatService, ShareUrlService} from '../../shared';
import {
  buildHeatmapTiles,
  getStartDateFor,
  getTileColor,
  getTileFontSize,
  getTooltipStyle,
  getTodayIso,
  HeatmapIndex,
  HeatmapTile,
  layoutHeatmapTreemap,
  SectorGroup,
  shouldShowTicker,
  shouldShowVariance,
} from './stocks-heatmaps.utils';

@Component({
  selector: 'app-stocks-heatmaps',
  imports: [],
  templateUrl: './stocks-heatmaps.html',
  styleUrl: './stocks-heatmaps.scss',
})
export class StocksHeatmaps implements OnDestroy {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly httpClient = inject(HttpClient);
  private readonly statsService = inject(MarketsStatsService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly dateFormatService = inject(DateFormatService);
  private readonly shareUrlService = inject(ShareUrlService);
  private readonly containerRef = viewChild<ElementRef>('heatmapContainer');

  readonly selectedIndex = signal<HeatmapIndex>('sp500');
  readonly loading = signal(true);
  readonly sectorGroups = signal<SectorGroup[]>([]);
  readonly zoomedSector = signal<string | null>(null);
  readonly hoveredTile = signal<HeatmapTile | null>(null);
  readonly mouseX = signal(0);
  readonly mouseY = signal(0);
  readonly heatmapDate = signal<string>('');
  readonly hasPointer = this.isBrowser && typeof globalThis.matchMedia === 'function' && globalThis.matchMedia('(hover: hover)').matches;

  readonly tooltipStyle = computed(() => {
    return getTooltipStyle(
      this.mouseX(),
      this.mouseY(),
      this.containerWidth || 1200,
      this.containerHeight || 700,
    );
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
    if (this.isBrowser) {
      this.loadData();
      this.setupResize();
    }
  }

  ngOnDestroy() {
    this.resizeObserver?.disconnect();
    this.shareUrlService.update({title: '', url: ''});
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
    return getTileColor(pv);
  }

  tileFontSize(tile: HeatmapTile): number {
    return getTileFontSize(tile);
  }

  showTicker(tile: HeatmapTile): boolean {
    return shouldShowTicker(tile);
  }

  showVariance(tile: HeatmapTile): boolean {
    return shouldShowVariance(tile);
  }

  formatDate(dateStr: string): string {
    return this.dateFormatService.format(dateStr);
  }

  private updateShareUrl(): void {
    if (this.isBrowser) {
      this.shareUrlService.update({
        title: `Stocks Heatmap - ${this.formatDate(this.heatmapDate())}`,
        url: `${globalThis.location.origin}/markets/stocks?date=${this.heatmapDate()}`,
      });
    }
  }

  private todayISO(): string {
    return getTodayIso();
  }

  private startDateFor(endDate: string): string {
    return getStartDateFor(endDate);
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
      const dateParam = this.route.snapshot.queryParamMap.get('date');
      const endDate = dateParam || undefined;
      const startDate = endDate ? this.startDateFor(endDate) : undefined;

      forkJoin({
        stats: this.statsService.getStatsCloseBulk('quaks_stocks-eod_latest', tickers, startDate, endDate),
        caps: this.statsService.getMarketCapsBulk('quaks_stocks-metadata_latest', tickers),
      }).subscribe(({stats, caps}) => {
        const {tiles, mostRecentDate} = buildHeatmapTiles(constituents, stats, caps);
        this.allTiles = tiles;
        if (mostRecentDate) this.heatmapDate.set(mostRecentDate);
        this.updateShareUrl();
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
    this.sectorGroups.set(
      layoutHeatmapTreemap(
        tiles,
        this.containerWidth || 1200,
        this.containerHeight || 700,
        this.zoomedSector(),
      ),
    );
  }
}
