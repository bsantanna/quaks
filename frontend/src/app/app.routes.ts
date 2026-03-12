import { Routes } from '@angular/router';
import {MarketsStocksDashboard} from './page-markets-stocks-dashboard';
import {PageTerms} from './page-terms';
import {PageCookies} from './page-cookies';
import {MarketsNewsRelated} from './page-markets-news-related';
import {MarketsPerformanceComparison} from './page-markets-performance-comparison';
import {MarketsNewsItem} from './page-markets-news-item';
import {MarketsStocks} from './page-markets-stocks';
import {MarketsNews} from './page-markets-news';
import {MarketsProfile} from './page-markets-profile/markets-profile';
import {InsightsStocksReport} from './page-insights-stocks-report/insights-stocks-report';
import {InsightsStocks} from './page-insights-stocks/insights-stocks';
import {InsightsAgents} from './page-insights-agents/insights-agents';
import {InsightsProfile} from './page-insights-profile/insights-profile';
import {InsightsNews} from './page-insights-news/insights-news';
import {InsightsNewsItem} from './page-insights-news-item/insights-news-item';

export const routes: Routes = [
  {
    title: 'Insights',
    path: 'insights',
    children: [
      {
        title: 'Insights Agents',
        path: 'agents',
        component: InsightsAgents
      },
      {
        title: 'Insights Agent Profile',
        path: 'profile/:agentName',
        component: InsightsProfile
      },
      {
        title: 'News Insights',
        path: 'news',
        component: InsightsNews
      },
      {
        title: 'News Insight',
        path: 'news/item/:indexName/:newsItemId',
        component: InsightsNewsItem
      },
      {
        title: 'Stocks Insights',
        path: 'stocks',
        component: InsightsStocks
      },
      {
        title: 'Stocks Insights Report',
        path: 'stocks/:keyTicker',
        component: InsightsStocksReport
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
