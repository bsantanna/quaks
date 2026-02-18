import { Routes } from '@angular/router';
import {MarketsStocksDashboard} from './page-markets-stocks-dashboard/markets-stocks-dashboard.component';
import { PageTerms } from './page-terms/page-terms';
import {MarketsNewsRelated} from './page-markets-news-related/markets-news-related';
import {MarketsPerformanceComparison} from './page-markets-performance-comparison/markets-performance-comparison';
import {InsightsQuaksStocksExpert} from './page-insights-quaks-stocks-expert/insights-quaks-stocks-expert';
import {MarketsNewsItem} from './page-markets-news-item/markets-news-item.component';
import {MarketsStocks} from './page-markets-stocks/markets-stocks';
import {MarketsNews} from './page-markets-news/markets-news';

export const routes: Routes = [
  {
    title: 'Insights',
    path: 'insights',
    children: [
      {
        title: 'AI Stocks Experts',
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
        title: 'News',
        path: 'news',
        component: MarketsNews
      },
      {
        title: 'Article',
        path: 'news/item/:indexName/:newsItemId',
        component: MarketsNewsItem
      },
      {
        title: 'News feed',
        path: 'news/related/:keyTicker',
        component: MarketsNewsRelated
      },
      {
        title: 'Stocks',
        path: 'stocks',
        component: MarketsStocks
      },
      {
        title: 'Stocks Dashboard',
        path: 'stocks/:keyTicker',
        component: MarketsStocksDashboard
      }
    ]
  },
  {
    title: 'Terms of Service',
    path: 'terms',
    component: PageTerms
  },
  { path: '**', redirectTo: '' }
];
