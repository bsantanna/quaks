#!/usr/bin/env python3
"""Generates frontend/public/sitemap.xml from the indexed ticker list."""

import json
import os

BASE_URL = "https://quaks.ai"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TICKER_FILE = os.path.join(
    PROJECT_ROOT, "frontend/public/json/indexed_key_ticker_list.json"
)
SITEMAP_FILE = os.path.join(PROJECT_ROOT, "frontend/public/sitemap.xml")

STATIC_ROUTES = [
    ("/", "daily", "1.0"),
    ("/markets/stocks", "daily", "0.9"),
    ("/markets/news", "hourly", "0.9"),
    ("/markets/performance", "daily", "0.8"),
    ("/terms", "monthly", "0.3"),
]

with open(TICKER_FILE) as f:
    tickers = json.load(f)

urls = []
for path, freq, priority in STATIC_ROUTES:
    urls.append(
        f"  <url>\n"
        f"    <loc>{BASE_URL}{path}</loc>\n"
        f"    <changefreq>{freq}</changefreq>\n"
        f"    <priority>{priority}</priority>\n"
        f"  </url>"
    )

for t in tickers:
    urls.append(
        f"  <url>\n"
        f"    <loc>{BASE_URL}/markets/stocks/{t['key_ticker']}</loc>\n"
        f"    <changefreq>daily</changefreq>\n"
        f"    <priority>0.7</priority>\n"
        f"  </url>"
    )

sitemap = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(urls)
    + "\n</urlset>\n"
)

with open(SITEMAP_FILE, "w") as f:
    f.write(sitemap)

print(f"sitemap.xml generated: {len(urls)} URLs")
