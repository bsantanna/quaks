import { Routes } from '@angular/router';
import {MarketsStocksEodDashboard} from './page-markets-stocks-eod-dashboard/markets-stocks-eod-dashboard';
import { PageTerms } from './page-terms/page-terms';
import {MarketsNewsRelated} from './page-markets-news-related/markets-news-related';
import {MarketsPerformanceComparison} from './page-markets-performance-comparison/markets-performance-comparison';
import {InsightsQuaksStocksExpert} from './page-insights-quaks-stocks-expert/insights-quaks-stocks-expert';

export const routes: Routes = [
  {
    title: 'Insights',
    path: 'insights',
    children: [
      {
        title: 'Quaks Stocks Experts',
        path: 'qse/:keyTicker',
        component: InsightsQuaksStocksExpert
      },
    ]
  },
  {
    title: 'Markets',
    path: 'markets',
    children: [
      {
        title: 'Performance comparison',
        path: 'performance/:keyTicker',
        component: MarketsPerformanceComparison
      },
      {
        title: 'News feed',
        path: 'news/related/:keyTicker',
        component: MarketsNewsRelated
      },
      {
        title: 'Stock Dashboard',
        path: 'stocks/:keyTicker',
        component: MarketsStocksEodDashboard
      }
    ]
  },
  {
    title: '',
    path: 'terms',
    component: PageTerms
  },
  { path: '**', redirectTo: '' }
];
