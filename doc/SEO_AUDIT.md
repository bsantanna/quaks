# SEO Audit Report — Quaks Platform

**Date:** 2026-03-06 (update 3)
**Previous Audit:** 2026-03-05 (update 2)
**Estimated Lighthouse SEO Score:** ~92/100 (up from ~90)

---

## Resolved (All Time)

| # | Issue | Resolution |
|---|-------|------------|
| 1 | Hash routing (`/#/`) | `withHashLocation()` removed. Path-based routing active. |
| 2 | No robots.txt | Added to `frontend/public/robots.txt`. |
| 3 | No sitemap.xml | Added to `frontend/public/sitemap.xml` with per-ticker pages. |
| 4 | No meta description | In `index.html` + `SeoService` per route. |
| 5 | No Open Graph / Twitter Cards | Full OG + Twitter Card tags, dynamically updated. |
| 6 | No structured data (JSON-LD) | `WebApplication` schema in `index.html`. |
| 6b | No per-page structured data for news | `NewsArticle` JSON-LD injected by `SeoService.setNewsArticleSchema()` on news item pages. Cleaned up on navigation away. |
| 7 | Multiple H1 tags in nav header | Fixed — no H1 in navigation-header. |
| 8 | No `<main>` landmark | `<main id="main-content">` wraps router-outlet. |
| 9 | No canonical URLs | `SeoService` dynamically sets `<link rel="canonical">`. |
| 10 | Static page title | `SeoService` sets unique `<title>` per route. |
| 12 | No skip-navigation link | Added `<a href="#main-content" class="sr-only focus:not-sr-only ...">Skip to main content</a>` in `app.html`. |
| 14 | No Web App Manifest | `manifest.webmanifest` with icons (192x192, 512x512). |
| 15 | No favicon set | Full set: 16x16, 32x32, 180x180, 192x192, 512x512, apple-touch-icon, mask-icon. |

### Resolved This Session

| # | Issue | What Changed |
|---|-------|------------|
| 16 | Stub content on Stocks page | Replaced `<p>markets-stocks works!</p>` with full heatmap component (`StocksHeatmaps`). Page now has rich interactive content (S&P 500 / NASDAQ 100 treemap heatmaps). `SeoService` called with title "Stocks" and relevant description. |

---

## Still Open

### High

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 6c | **No BreadcrumbList schema** | All nested routes | No breadcrumb display in search results. |

### Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 11 | **No `prefers-reduced-motion` CSS** | `styles.scss` | Accessibility gap for motion-sensitive users. |
| 17 | **No `font-display: swap`** | Global styles | Minor LCP impact if custom fonts load slowly. |
| 19 | **No SSR/prerendering** | Entire SPA | Crawlers see empty `<app-root>` until JS executes. Google renders JS but other engines may not. |
| 20 | **No `TitleStrategy`** | `app.config.ts` | Route `title` properties don't auto-propagate. Works via manual `SeoService` calls, but no fallback for routes that forget to call it. |

### Low

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 13 | `stock-eod-insights.html` img `alt=""` without `aria-hidden` | Line 5 | Minor — `alt=""` is valid per WCAG for decorative images. |
| 18 | No `hreflang` tags | N/A | Only relevant if i18n is planned. |
| 21 | **Sitemap is static** | `frontend/public/sitemap.xml` (512KB+) | Large static file. Consider dynamic generation. |

---

## What's Working Well

- **SeoService**: Title, description, OG, Twitter, canonical, and now `NewsArticle` JSON-LD — all per-route. Used in all page components.
- **Skip navigation**: Keyboard-accessible skip link to `#main-content`.
- **Structured data**: `WebApplication` on homepage + `NewsArticle` on news item pages with proper cleanup on navigation.
- **ARIA attributes**: Well-implemented across components (39+ occurrences).
- **Image alt text**: Good coverage — decorative images use `aria-hidden="true" alt=""`, content images use descriptive alt.
- **Semantic HTML**: `<main>`, `<nav>`, `<footer>`, `<article>`, `<header>` used correctly.
- **H1 hierarchy**: Single H1 per content page, none in navigation.
- **FastAPI SPA fallback**: `StaticFiles(html=True)` for all frontend routes.
- **Path-based routing**: Clean URLs like `/markets/stocks/AAPL`.
- **robots.txt**: Blocks API endpoints, allows public pages.
- **sitemap.xml**: Comprehensive with all public URLs and per-ticker pages.
- **Full meta tag set**: Description, OG, Twitter Cards, canonical, theme-color.
- **PWA-ready**: Manifest, icons, apple-touch-icon, theme-color.
- **`lang="en"`**: Present on `<html>` tag.

---

## Recommended Next Steps (Priority Order)

1. **Add `prefers-reduced-motion`** to `styles.scss` — quick accessibility compliance
2. **Add `BreadcrumbList` schema** for nested routes — breadcrumb rich results
3. **Consider SSR/prerendering** for key landing pages — biggest remaining SEO uplift
4. **Add `font-display: swap`** if custom fonts are loaded
5. **Wire up `TitleStrategy`** as a fallback for routes that don't call `SeoService` manually

---

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/index.html` | Main HTML shell — meta tags, structured data, manifest link |
| `frontend/src/app/app.config.ts` | Angular providers — path routing (no hash) |
| `frontend/src/app/app.routes.ts` | Route definitions with `title` properties |
| `frontend/src/app/app.html` | App shell with `<main>` landmark + skip-nav link |
| `frontend/src/app/shared/services/seo.service.ts` | Dynamic SEO meta tag + JSON-LD service |
| `frontend/src/app/page-markets-news-item/markets-news-item.component.ts` | News item — calls `setNewsArticleSchema()` |
| `frontend/public/` | Static assets — robots.txt, sitemap.xml, manifest, icons |
| `frontend/angular.json` | Build config — assets array |
| `app/main.py` | FastAPI — static files mount with SPA fallback |
| `frontend/src/styles.scss` | Global styles — a11y improvements needed |

## Scoring Targets

| Tool | Current (est.) | Target |
|------|----------------|--------|
| Google Lighthouse SEO | ~90 | 100 |
| Google Lighthouse Accessibility | ~85 | 95+ |
| Google Lighthouse Performance | ~80 | 90+ |
| Google PageSpeed Insights (Mobile) | ~75 | 90+ |
