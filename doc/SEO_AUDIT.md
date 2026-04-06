# SEO Audit Report — Quaks Platform

**Date:** 2026-04-06 (update 5)
**Previous Audit:** 2026-03-09 (update 4)
**Estimated Lighthouse SEO Score:** ~96/100 (up from ~92)

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
| 11 | No `prefers-reduced-motion` CSS | `@media (prefers-reduced-motion: reduce)` at line 118 in `styles.scss`. |
| 12 | No skip-navigation link | Added `<a href="#main-content" class="sr-only focus:not-sr-only ...">Skip to main content</a>` in `app.html`. |
| 14 | No Web App Manifest | `manifest.webmanifest` with icons (192x192, 512x512). |
| 15 | No favicon set | Full set: 16x16, 32x32, 180x180, 192x192, 512x512, apple-touch-icon, mask-icon. |
| 16 | Stub content on Stocks page | Replaced with full heatmap component (`StocksHeatmaps`). |
| 6c | No BreadcrumbList schema | `SeoService.update()` auto-generates `BreadcrumbList` JSON-LD from the `path` param. Cleaned up on `reset()`. |

---

## Audit Corrections (Update 5)

| # | Issue | Resolution |
|---|-------|------------|
| 22 | **Cookies page** | No separate `/cookies` route needed. `/privacy` already contains the full GDPR cookie policy (ePrivacy, legal basis, cookie table, retention, rights). Audit incorrectly marked this as resolved via a new page in update 4. |
| 23 | **Cookie management UX** | Working correctly: footer "Cookies" button opens the consent dialog via `manageCookies()`. Cookie consent dialog links to `/privacy`. No new page required. |
| 17 | **Font loading** | Resolved: Google Fonts `@import` removed from `styles.scss`. Fonts now loaded via `<link rel="preconnect">` + `<link rel="stylesheet">` in `index.html`. |
| 21 | **Sitemap incomplete** | Resolved: Added `/insights/agents`, `/insights/news`, `/insights/financial`, `/waitlist` to `sitemap.xml`. |

---

## Still Open

### Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 19 | **No SSR/prerendering** | Entire SPA | Crawlers see empty `<app-root>` until JS executes. Google renders JS but other engines may not. Biggest remaining SEO uplift. |
| 20 | **No `TitleStrategy`** | `app.config.ts` | Route `title` properties don't auto-propagate. Works via manual `SeoService` calls, but no fallback for routes that forget to call it. |

### Low

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 13 | `stock-eod-insights.html` img `alt=""` without `aria-hidden` | Line 5 | Minor — `alt=""` is valid per WCAG for decorative images. |
| 18 | No `hreflang` tags | N/A | Only relevant if i18n is planned. |
| 24 | **`page-terms.html` hardcoded text colors** | `text-gray-100` | Not theme-aware. Works on dark themes but won't adapt to light themes. |

---

## What's Working Well

- **SeoService**: Title, description, OG, Twitter, canonical, BreadcrumbList, NewsArticle JSON-LD — per-route. Used in 15+ components.
- **Skip navigation**: Keyboard-accessible skip link to `#main-content`.
- **Structured data**: `WebApplication` on homepage + `NewsArticle` on news item pages with proper cleanup.
- **ARIA attributes**: Well-implemented across components (39+ occurrences).
- **Image alt text**: Good coverage — decorative images use `aria-hidden="true" alt=""`, content images use descriptive alt.
- **Semantic HTML**: `<main>`, `<nav>`, `<footer>`, `<article>`, `<header>` used correctly.
- **H1 hierarchy**: Single H1 per content page, none in navigation.
- **FastAPI SPA fallback**: `StaticFiles(html=True)` for all frontend routes.
- **Path-based routing**: Clean URLs like `/markets/stocks/AAPL`.
- **robots.txt**: Blocks API + internal endpoints, allows public pages. References sitemap.
- **Full meta tag set**: Description, OG, Twitter Cards, canonical, theme-color in `index.html`.
- **PWA-ready**: Manifest, icons, apple-touch-icon, theme-color.
- **`lang="en"`**: Present on `<html>` tag.
- **`prefers-reduced-motion`**: Media query in `styles.scss` disables animations for motion-sensitive users.
- **Google Fonts**: `display=swap` parameter set in import URLs (font-display honored).

---

## Recommended Next Steps (Priority Order)

1. **Wire up `TitleStrategy`** — Fallback for routes that don't call `SeoService` manually.
2. **Consider SSR/prerendering** — Angular Universal or static prerender for key landing pages. Biggest long-term SEO uplift.

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
| `frontend/src/styles.scss` | Global styles — font imports, theme vars, a11y media queries |
| `app/main.py` | FastAPI — static files mount with SPA fallback |

## Scoring Targets

| Tool | Current (est.) | Target |
|------|----------------|--------|
| Google Lighthouse SEO | ~92 | 100 |
| Google Lighthouse Accessibility | ~85 | 95+ |
| Google Lighthouse Performance | ~80 | 90+ |
| Google PageSpeed Insights (Mobile) | ~75 | 90+ |
