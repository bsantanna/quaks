import { Routes } from '@angular/router';
import {MarketsStocksDashboard} from './page-markets-stocks-dashboard/markets-stocks-dashboard.component';
import { PageTerms } from './page-terms/page-terms';
import {MarketsNewsRelated} from './page-markets-news-related/markets-news-related';
import {MarketsPerformanceComparison} from './page-markets-performance-comparison/markets-performance-comparison';
import {InsightsQuaksStocksExpert} from './page-insights-quaks-stocks-expert/insights-quaks-stocks-expert';
import {MarketsNewsItem} from './page-markets-news-item/markets-news-item.component';

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
        title: 'Quaks - Performance comparison',
        path: 'performance/:keyTicker',
        component: MarketsPerformanceComparison
      },
      {
        title: 'Quaks - News',
        path: 'news/item/:indexName/:newsItemId',
        component: MarketsNewsItem
      },
      {
        title: 'Quaks - News feed',
        path: 'news/related/:keyTicker',
        component: MarketsNewsRelated
      },
      {
        title: 'Quaks - Stock Dashboard',
        path: 'stocks/:keyTicker',
        component: MarketsStocksDashboard
      }
    ]
  },
  {
    title: 'Quaks - Terms of Service',
    path: 'terms',
    component: PageTerms
  },
  { path: '**', redirectTo: '' }
];
