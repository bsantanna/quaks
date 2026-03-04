import {Component, inject, signal, OnInit, OnDestroy} from '@angular/core';
import {ActivatedRoute, Router} from '@angular/router';
import {Subscription} from 'rxjs';

@Component({
  selector: 'app-markets-performance-comparison',
  imports: [],
  templateUrl: './markets-performance-comparison.html',
  styleUrl: './markets-performance-comparison.scss',
})
export class MarketsPerformanceComparison implements OnInit, OnDestroy {

  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private queryParamSub!: Subscription;

  readonly symbols = signal<string[]>([]);

  ngOnInit() {
    this.queryParamSub = this.route.queryParamMap.subscribe(params => {
      const q = params.get('q');
      this.symbols.set(q ? q.split(',').map(s => s.trim()).filter(s => s.length > 0) : []);
    });
  }

  ngOnDestroy() {
    this.queryParamSub.unsubscribe();
  }

  updateSymbols(symbols: string[]) {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {q: symbols.join(',')},
      queryParamsHandling: 'replace',
    });
  }

}
