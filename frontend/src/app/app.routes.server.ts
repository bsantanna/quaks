import { RenderMode, ServerRoute } from '@angular/ssr';

export const serverRoutes: ServerRoute[] = [
  {
    path: 'markets/stocks',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'markets/news',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'markets/performance',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'terms',
    renderMode: RenderMode.Prerender
  },
  {
    path: 'cookies',
    renderMode: RenderMode.Prerender
  },
  {
    path: '**',
    renderMode: RenderMode.Client
  }
];
