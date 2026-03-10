import { Routes } from '@angular/router';
import {MarketsStocksDashboard} from './page-markets-stocks-dashboard';
import {PageTerms} from './page-terms';
import {PageCookies} from './page-cookies';
import {MarketsNewsRelated} from './page-markets-news-related';
import {MarketsPerformanceComparison} from './page-markets-performance-comparison';
import {InsightsQuaksStocksExpert} from './page-insights-quaks-stocks-expert';
import {MarketsNewsItem} from './page-markets-news-item';
import {MarketsStocks} from './page-markets-stocks';
import {MarketsNews} from './page-markets-news';
import {MarketsProfile} from './page-markets-profile/markets-profile';

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
        path: 'performance',
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
        title: 'Stocks Market',
        path: 'stocks',
        component: MarketsStocks
      },
      {
        title: 'Stocks Dashboard',
        path: 'stocks/:keyTicker',
        component: MarketsStocksDashboard
      },
      {
        title: 'Company Profile',
        path: 'profile/:keyTicker',
        component: MarketsProfile
      }
    ]
  },
  {
    title: 'Terms of Service',
    path: 'terms',
    component: PageTerms
  },
  {
    title: 'Cookie Policy',
    path: 'cookies',
    component: PageCookies
  },
  { path: '**', redirectTo: '' }
];
