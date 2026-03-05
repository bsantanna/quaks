# SEO Audit Report — Quaks Platform

**Date:** 2026-03-05
**Estimated Lighthouse SEO Score:** ~35/100

---

## Critical (Blocks indexing entirely)

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1 | **Hash routing (`/#/`)** | `frontend/src/app/app.config.ts` — `withHashLocation()` | Search engines cannot crawl any route. All pages invisible. |
| 2 | **No robots.txt** | Missing from `frontend/public/` | Crawlers have no guidance. |
| 3 | **No sitemap.xml** | Missing from `frontend/public/` | Crawlers can't discover pages. |
| 4 | **No meta description** | Not in `index.html`, no `Meta` service | Empty SERP snippets. |

## High (Severely hurts ranking)

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 5 | **No Open Graph / Twitter Cards** | Missing entirely from `index.html` | No rich previews when shared on social media. |
| 6 | **No structured data (JSON-LD)** | Missing | No rich results in SERPs. |
| 7 | **Multiple H1 tags per page** | `navigation-header.html` has 3x `<h1>` | Confuses crawlers on page topic. |
| 8 | **No `<main>` landmark** | `app.html` uses `<div>` wrapper | Accessibility violation, hurts a11y score. |
| 9 | **No canonical URLs** | Missing `<link rel="canonical">` | Risk of duplicate content penalties. |
| 10 | **Static page title** | Always "Quaks" in browser tab | Route `title` exists but doesn't propagate to `<title>` without Title strategy. |

## Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 11 | No `prefers-reduced-motion` CSS | `styles.scss` | Accessibility gap. |
| 12 | No skip-navigation link | `app.html` | Keyboard users can't skip to content. |
| 13 | Missing alt on 1 image | `stock-eod-insights.html` line 5 | a11y violation. |
| 14 | No Web App Manifest | Missing from `frontend/public/` | No PWA install, no theme color. |
| 15 | No favicon set (only .ico) | Single `favicon.ico` | Poor appearance on mobile bookmarks/tabs. |
| 16 | Some pages have stub content | `markets-stocks.html`: `<p>markets-stocks works!</p>` | Thin content penalty. |

## Low

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 17 | No `font-display: swap` | Relies on Tailwind defaults | Minor LCP impact. |
| 18 | No `hreflang` tags | N/A unless i18n planned | Future concern. |

---

## What's Already Good

- **ARIA attributes**: 39 occurrences across 11 files — well implemented
- **Image alt text**: 73% coverage with proper `aria-hidden` on decorative images
- **Semantic footer/nav**: Properly using `<footer>`, `<nav>` with aria-labels
- **News article page**: Uses `<header>` and `<article>` correctly
- **Screen-reader headings**: `<h2 class="sr-only">` used on dashboard pages
- **FastAPI SPA fallback**: `StaticFiles(html=True)` already handles SPA routing server-side
- **Route titles defined**: All routes have `title` properties in `app.routes.ts`
- **`lang="en"`**: Present on `<html>` tag

---

## Recommended Implementation Order

1. **Remove `withHashLocation()`** — FastAPI already has `html=True` SPA fallback, so path routing works immediately
2. **Add robots.txt + sitemap.xml** to `frontend/public/`
3. **Enrich index.html** — meta description, OG tags, Twitter Cards, JSON-LD, canonical, theme-color, manifest link
4. **Create SeoService** — Angular service using `Meta` + `Title` to set per-route tags dynamically
5. **Fix heading hierarchy** — Change nav H1s to `<span>` or `<p>`, ensure single H1 per page
6. **Add `<main>` to app.html** — Wrap router-outlet in semantic landmark
7. **Add manifest.webmanifest + favicon set**
8. **Accessibility pass** — skip-nav link, reduced-motion, focus styles
9. **Consider SSR/prerendering** — For crawler-friendly HTML on key landing pages

---

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/index.html` | Main HTML shell — meta tags, structured data, manifest link |
| `frontend/src/app/app.config.ts` | Angular providers — hash routing config |
| `frontend/src/app/app.routes.ts` | Route definitions with `title` properties |
| `frontend/src/app/app.html` | App shell — needs `<main>` landmark |
| `frontend/src/app/navigation-header/navigation-header.html` | Multiple H1 issue |
| `frontend/public/` | Static assets — robots.txt, sitemap.xml, manifest, icons |
| `frontend/angular.json` | Build config — assets array |
| `app/main.py` | FastAPI — static files mount with SPA fallback |
| `frontend/src/styles.scss` | Global styles — a11y improvements needed |

## Scoring Targets

| Tool | Current (est.) | Target |
|------|----------------|--------|
| Google Lighthouse SEO | ~35 | 100 |
| Google Lighthouse Accessibility | ~70 | 95+ |
| Google Lighthouse Performance | ~80 | 90+ |
| Google PageSpeed Insights (Mobile) | ~70 | 90+ |
