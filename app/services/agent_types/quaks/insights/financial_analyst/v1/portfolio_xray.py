from __future__ import annotations

from app.services.markets_stats import MarketsStatsService

_TABLE_OPEN = "<table>"
_TABLE_CLOSE = "</table>"
_NOT_CLASSIFIED = "Not Classified"

# --- Sector constants ---
_BASIC_MATERIALS = "Basic Materials"
_COMMUNICATION_SERVICES = "Communication Services"
_CONSUMER_CYCLICAL = "Consumer Cyclical"
_CONSUMER_DEFENSIVE = "Consumer Defensive"
_FINANCIAL_SERVICES = "Financial Services"
_REAL_ESTATE = "Real Estate"

# --- Region constants ---
_AMERICAS = "Americas"
_UNITED_STATES = "United States"
_CENTRAL_LATIN_AMERICA = "Central & Latin America"
_GREATER_EUROPE = "Greater Europe"
_UNITED_KINGDOM = "United Kingdom"
_WESTERN_EUROPE_EURO = "Western Europe - Euro"
_WESTERN_EUROPE_NON_EURO = "Western Europe - Non Euro"
_EMERGING_EUROPE = "Emerging Europe"
_MIDDLE_EAST_AFRICA = "Middle East / Africa"
_GREATER_ASIA = "Greater Asia"
_EMERGING_4_TIGERS = "Emerging 4 Tigers"
_EMERGING_ASIA_EX_4_TIGERS = "Emerging Asia - Ex 4 Tigers"

SUPERSECTOR_SECTORS = {
    "Cyclical": [
        _BASIC_MATERIALS,
        _CONSUMER_CYCLICAL,
        _FINANCIAL_SERVICES,
        _REAL_ESTATE,
    ],
    "Sensitive": [_COMMUNICATION_SERVICES, "Energy", "Industrials", "Technology"],
    "Defensive": [_CONSUMER_DEFENSIVE, "Healthcare", "Utilities"],
}

COUNTRY_REGION = {
    "US": (_AMERICAS, _UNITED_STATES),
    "USA": (_AMERICAS, _UNITED_STATES),
    "United States": (_AMERICAS, _UNITED_STATES),
    "Canada": (_AMERICAS, "Canada"),
    "CA": (_AMERICAS, "Canada"),
    "Brazil": (_AMERICAS, _CENTRAL_LATIN_AMERICA),
    "Mexico": (_AMERICAS, _CENTRAL_LATIN_AMERICA),
    "Argentina": (_AMERICAS, _CENTRAL_LATIN_AMERICA),
    "Chile": (_AMERICAS, _CENTRAL_LATIN_AMERICA),
    "Colombia": (_AMERICAS, _CENTRAL_LATIN_AMERICA),
    "Peru": (_AMERICAS, _CENTRAL_LATIN_AMERICA),
    "United Kingdom": (_GREATER_EUROPE, _UNITED_KINGDOM),
    "Germany": (_GREATER_EUROPE, _WESTERN_EUROPE_EURO),
    "France": (_GREATER_EUROPE, _WESTERN_EUROPE_EURO),
    "Netherlands": (_GREATER_EUROPE, _WESTERN_EUROPE_EURO),
    "Spain": (_GREATER_EUROPE, _WESTERN_EUROPE_EURO),
    "Italy": (_GREATER_EUROPE, _WESTERN_EUROPE_EURO),
    "Belgium": (_GREATER_EUROPE, _WESTERN_EUROPE_EURO),
    "Ireland": (_GREATER_EUROPE, _WESTERN_EUROPE_EURO),
    "Finland": (_GREATER_EUROPE, _WESTERN_EUROPE_EURO),
    "Austria": (_GREATER_EUROPE, _WESTERN_EUROPE_EURO),
    "Portugal": (_GREATER_EUROPE, _WESTERN_EUROPE_EURO),
    "Switzerland": (_GREATER_EUROPE, _WESTERN_EUROPE_NON_EURO),
    "Sweden": (_GREATER_EUROPE, _WESTERN_EUROPE_NON_EURO),
    "Norway": (_GREATER_EUROPE, _WESTERN_EUROPE_NON_EURO),
    "Denmark": (_GREATER_EUROPE, _WESTERN_EUROPE_NON_EURO),
    "Poland": (_GREATER_EUROPE, _EMERGING_EUROPE),
    "Czech Republic": (_GREATER_EUROPE, _EMERGING_EUROPE),
    "Hungary": (_GREATER_EUROPE, _EMERGING_EUROPE),
    "Russia": (_GREATER_EUROPE, _EMERGING_EUROPE),
    "Turkey": (_GREATER_EUROPE, _EMERGING_EUROPE),
    "Israel": (_GREATER_EUROPE, _MIDDLE_EAST_AFRICA),
    "South Africa": (_GREATER_EUROPE, _MIDDLE_EAST_AFRICA),
    "Saudi Arabia": (_GREATER_EUROPE, _MIDDLE_EAST_AFRICA),
    "Japan": (_GREATER_ASIA, "Japan"),
    "Australia": (_GREATER_ASIA, "Australasia"),
    "New Zealand": (_GREATER_ASIA, "Australasia"),
    "Taiwan": (_GREATER_ASIA, _EMERGING_4_TIGERS),
    "South Korea": (_GREATER_ASIA, _EMERGING_4_TIGERS),
    "Hong Kong": (_GREATER_ASIA, _EMERGING_4_TIGERS),
    "Singapore": (_GREATER_ASIA, _EMERGING_4_TIGERS),
    "China": (_GREATER_ASIA, _EMERGING_ASIA_EX_4_TIGERS),
    "India": (_GREATER_ASIA, _EMERGING_ASIA_EX_4_TIGERS),
    "Indonesia": (_GREATER_ASIA, _EMERGING_ASIA_EX_4_TIGERS),
    "Malaysia": (_GREATER_ASIA, _EMERGING_ASIA_EX_4_TIGERS),
    "Thailand": (_GREATER_ASIA, _EMERGING_ASIA_EX_4_TIGERS),
    "Philippines": (_GREATER_ASIA, _EMERGING_ASIA_EX_4_TIGERS),
    "Vietnam": (_GREATER_ASIA, _EMERGING_ASIA_EX_4_TIGERS),
}

REGION_SUBREGIONS = {
    _AMERICAS: [_UNITED_STATES, "Canada", _CENTRAL_LATIN_AMERICA],
    _GREATER_EUROPE: [
        _UNITED_KINGDOM,
        _WESTERN_EUROPE_EURO,
        _WESTERN_EUROPE_NON_EURO,
        _EMERGING_EUROPE,
        _MIDDLE_EAST_AFRICA,
    ],
    _GREATER_ASIA: [
        "Japan",
        "Australasia",
        _EMERGING_4_TIGERS,
        _EMERGING_ASIA_EX_4_TIGERS,
    ],
}

# Finnhub sector values (from ES metadata) → Morningstar super-sector parent
INDUSTRY_TO_SECTOR = {
    # Technology (Sensitive)
    "Technology": "Technology",
    "Semiconductors": "Technology",
    "Electrical Equipment": "Technology",
    # Communication Services (Sensitive)
    "Media": _COMMUNICATION_SERVICES,
    "Communications": _COMMUNICATION_SERVICES,
    "Telecommunication": _COMMUNICATION_SERVICES,
    # Energy (Sensitive)
    "Energy": "Energy",
    # Industrials (Sensitive)
    "Machinery": "Industrials",
    "Aerospace & Defense": "Industrials",
    "Airlines": "Industrials",
    "Road & Rail": "Industrials",
    "Marine": "Industrials",
    "Logistics & Transportation": "Industrials",
    "Transportation Infrastructure": "Industrials",
    "Construction": "Industrials",
    "Building": "Industrials",
    "Industrial Conglomerates": "Industrials",
    "Professional Services": "Industrials",
    "Commercial Services & Supplies": "Industrials",
    "Trading Companies & Distributors": "Industrials",
    "Packaging": "Industrials",
    # Financial Services (Cyclical)
    _FINANCIAL_SERVICES: _FINANCIAL_SERVICES,
    "Banking": _FINANCIAL_SERVICES,
    "Insurance": _FINANCIAL_SERVICES,
    # Consumer Cyclical (Cyclical)
    "Retail": _CONSUMER_CYCLICAL,
    "Hotels, Restaurants & Leisure": _CONSUMER_CYCLICAL,
    "Textiles, Apparel & Luxury Goods": _CONSUMER_CYCLICAL,
    "Automobiles": _CONSUMER_CYCLICAL,
    "Auto Components": _CONSUMER_CYCLICAL,
    "Leisure Products": _CONSUMER_CYCLICAL,
    "Diversified Consumer Services": _CONSUMER_CYCLICAL,
    "Consumer products": _CONSUMER_CYCLICAL,
    # Real Estate (Cyclical)
    _REAL_ESTATE: _REAL_ESTATE,
    # Basic Materials (Cyclical)
    "Metals & Mining": _BASIC_MATERIALS,
    "Chemicals": _BASIC_MATERIALS,
    "Paper & Forest": _BASIC_MATERIALS,
    # Healthcare (Defensive)
    "Health Care": "Healthcare",
    "Biotechnology": "Healthcare",
    "Pharmaceuticals": "Healthcare",
    "Life Sciences Tools & Services": "Healthcare",
    # Consumer Defensive (Defensive)
    "Food Products": _CONSUMER_DEFENSIVE,
    "Beverages": _CONSUMER_DEFENSIVE,
    "Tobacco": _CONSUMER_DEFENSIVE,
    "Distributors": _CONSUMER_DEFENSIVE,
    # Utilities (Defensive)
    "Utilities": "Utilities",
}

# Build lookup of known sector names for fast membership check
_KNOWN_SECTORS = set()
for _sectors in SUPERSECTOR_SECTORS.values():
    _KNOWN_SECTORS.update(_sectors)

# Keyword hints for fuzzy fallback when exact match fails
_SECTOR_KEYWORDS = {
    "Technology": [
        "tech",
        "software",
        "semiconductor",
        "computer",
        "electronic",
        "solar",
        "cyber",
    ],
    _COMMUNICATION_SERVICES: [
        "media",
        "telecom",
        "entertainment",
        "gaming",
        "advertis",
        "broadcast",
        "publish",
        "streaming",
    ],
    "Healthcare": ["health", "drug", "biotech", "medical", "pharma", "diagnostic"],
    _FINANCIAL_SERVICES: [
        "bank",
        "insurance",
        "capital",
        "credit",
        "asset management",
        "financial",
    ],
    _CONSUMER_CYCLICAL: [
        "retail",
        "auto",
        "restaurant",
        "apparel",
        "luxury",
        "travel",
        "hotel",
        "leisure",
    ],
    _CONSUMER_DEFENSIVE: [
        "food",
        "beverage",
        "grocery",
        "tobacco",
        "household",
        "discount",
    ],
    "Industrials": [
        "aerospace",
        "defense",
        "railroad",
        "airline",
        "freight",
        "waste",
        "construction",
        "industrial",
    ],
    "Energy": ["oil", "gas", "energy", "petroleum", "fuel"],
    "Utilities": ["utilit", "electric", "water", "renewable"],
    _REAL_ESTATE: ["reit", "real estate", "property"],
    _BASIC_MATERIALS: [
        "gold",
        "steel",
        "chemical",
        "copper",
        "mining",
        "lumber",
        "aluminum",
    ],
}


def _classify_size(market_cap: float) -> str:
    if market_cap > 10_000_000_000:
        return "Large"
    if market_cap > 2_000_000_000:
        return "Mid"
    return "Small"


def _classify_style(pe_ratio: float) -> str:
    if pe_ratio <= 0:
        return "Blend"
    if pe_ratio < 18:
        return "Value"
    if pe_ratio <= 25:
        return "Blend"
    return "Growth"


def _normalize_sector(raw_sector: str) -> str:
    if raw_sector in _KNOWN_SECTORS:
        return raw_sector
    mapped = INDUSTRY_TO_SECTOR.get(raw_sector)
    if mapped:
        return mapped
    # Fuzzy fallback: match keywords in the raw sector name
    lower = raw_sector.lower()
    for sector, keywords in _SECTOR_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return sector
    return _NOT_CLASSIFIED


def _build_style_table(style_grid: dict) -> list[str]:
    rows = [
        "<h3>Investment Style</h3>",
        _TABLE_OPEN,
        "<tr><th></th><th>Value</th><th>Blend</th><th>Growth</th></tr>",
    ]
    for size in ("Large", "Mid", "Small"):
        v, b, g = [
            f"{style_grid[(size, st)]:.0f}" for st in ("Value", "Blend", "Growth")
        ]
        rows.append(
            f"<tr><td><b>{size}</b></td><td>{v}</td><td>{b}</td><td>{g}</td></tr>"
        )
    rows.append(_TABLE_CLOSE)
    return rows


def _build_sector_table(sector_wt: dict) -> list[str]:
    rows = [
        "<h3>Stock Sectors</h3>",
        _TABLE_OPEN,
        "<tr><th>Sector</th><th>Weight %</th></tr>",
    ]
    for supersector, sectors in SUPERSECTOR_SECTORS.items():
        total = sum(sector_wt.get(s, 0) for s in sectors)
        rows.append(
            f"<tr><td><b>{supersector}</b></td><td><b>{total:.2f}</b></td></tr>"
        )
        for s in sectors:
            w = sector_wt.get(s, 0)
            if w > 0:
                rows.append(f"<tr><td>&nbsp;&nbsp;{s}</td><td>{w:.2f}</td></tr>")
    nc = sector_wt.get(_NOT_CLASSIFIED, 0)
    if nc > 0:
        rows.append(
            f"<tr><td><b>{_NOT_CLASSIFIED}</b></td><td><b>{nc:.2f}</b></td></tr>"
        )
    rows.append(_TABLE_CLOSE)
    return rows


def _build_region_table(subregion_wt: dict) -> list[str]:
    rows = [
        "<h3>World Regions</h3>",
        _TABLE_OPEN,
        "<tr><th>Region</th><th>Weight %</th></tr>",
    ]
    for region, subregions in REGION_SUBREGIONS.items():
        total = sum(subregion_wt.get(sr, 0) for sr in subregions)
        if total > 0:
            rows.append(f"<tr><td><b>{region}</b></td><td><b>{total:.2f}</b></td></tr>")
            for sr in subregions:
                w = subregion_wt.get(sr, 0)
                if w > 0:
                    rows.append(f"<tr><td>&nbsp;&nbsp;{sr}</td><td>{w:.2f}</td></tr>")
    nc = subregion_wt.get(_NOT_CLASSIFIED, 0)
    if nc > 0:
        rows.append(
            f"<tr><td><b>{_NOT_CLASSIFIED}</b></td><td><b>{nc:.2f}</b></td></tr>"
        )
    rows.append(_TABLE_CLOSE)
    return rows


def _build_stats_table(stat_keys: dict, avg_stats: dict) -> list[str]:
    rows = [
        "<h3>Stock Stats</h3>",
        _TABLE_OPEN,
        "<tr><th>Metric</th><th>Average</th></tr>",
    ]
    for key, label in stat_keys.items():
        val = f"{avg_stats[key]:.2f}" if avg_stats[key] > 0 else "-"
        rows.append(f"<tr><td>{label}</td><td>{val}</td></tr>")
    rows.append(_TABLE_CLOSE)
    return rows


def _build_composition_table(
    sorted_tickers: list, profiles: dict, weights: dict
) -> list[str]:
    rows = [
        "<h3>Composition</h3>",
        _TABLE_OPEN,
        "<tr><th>Name</th><th>Ticker</th><th>Sector</th><th>Country</th><th>Weight %</th></tr>",
    ]
    for ticker in sorted_tickers[:10]:
        p = profiles[ticker]
        rows.append(
            f"<tr><td>{p.get('name', ticker)}</td><td>({ticker})</td>"
            f"<td>{p.get('sector', '-')}</td><td>{p.get('country', '-')}</td>"
            f"<td>{weights[ticker]:.2f}</td></tr>"
        )
    rows.append(_TABLE_CLOSE)
    return rows


def _compute_weights(profiles, allocation, n):
    if allocation:
        raw_wt = {t: allocation.get(t, 0) for t in profiles}
        total = sum(raw_wt.values())
        weights = (
            {t: w * 100.0 / total for t, w in raw_wt.items()}
            if total > 0
            else {t: 100.0 / n for t in profiles}
        )
        return weights, True
    return {t: 100.0 / n for t in profiles}, False


def _compute_avg_stats(profiles, weights, stat_keys):
    avg_stats = {}
    for key in stat_keys:
        w_sum, w_total = 0.0, 0.0
        for ticker, p in profiles.items():
            val = p.get(key)
            if val is not None and val > 0:
                w_sum += val * weights[ticker]
                w_total += weights[ticker]
        avg_stats[key] = w_sum / w_total if w_total > 0 else 0
    return avg_stats


def compute_xray_data(
    markets_stats_service: MarketsStatsService,
    tickers: list[str],
    allocation: dict = None,
) -> dict:
    """Compute X-Ray structured data from ticker metadata. Deterministic — no LLM."""
    profiles = {}
    for ticker in tickers:
        profile = markets_stats_service.get_company_profile(
            index_name="quaks_stocks-metadata_latest",
            key_ticker=ticker,
        )
        if profile:
            profiles[ticker] = profile

    if not profiles:
        return {}

    n = len(profiles)
    weights, has_allocation = _compute_weights(profiles, allocation, n)

    style_grid = {
        (s, v): 0.0
        for s in ("Large", "Mid", "Small")
        for v in ("Value", "Blend", "Growth")
    }
    for ticker, p in profiles.items():
        mc = p.get("market_capitalization") or 0
        pe = p.get("forward_pe") or p.get("pe_ratio") or 0
        style_grid[(_classify_size(mc), _classify_style(pe))] += weights[ticker]

    sector_wt = {}
    for ticker, p in profiles.items():
        raw = p.get("sector") or _NOT_CLASSIFIED
        s = _normalize_sector(raw)
        sector_wt[s] = sector_wt.get(s, 0) + weights[ticker]

    subregion_wt = {}
    for ticker, p in profiles.items():
        c = p.get("country") or _NOT_CLASSIFIED
        _, sr = COUNTRY_REGION.get(c, (_NOT_CLASSIFIED, _NOT_CLASSIFIED))
        subregion_wt[sr] = subregion_wt.get(sr, 0) + weights[ticker]

    stat_keys = {
        "pe_ratio": "Trailing P/E",
        "forward_pe": "Forward P/E",
        "price_to_book_ratio": "Price/Book",
        "profit_margin": "Profit Margin %",
        "return_on_equity_ttm": "Return on Equity %",
        "dividend_yield": "Dividend Yield %",
        "beta": "Beta",
    }
    avg_stats = _compute_avg_stats(profiles, weights, stat_keys)

    sorted_tickers = sorted(
        profiles.keys(),
        key=lambda t: (weights[t], profiles[t].get("market_capitalization") or 0),
        reverse=True,
    )

    return {
        "profiles": profiles,
        "weights": weights,
        "has_allocation": has_allocation,
        "style_grid": style_grid,
        "sector_wt": sector_wt,
        "subregion_wt": subregion_wt,
        "stat_keys": stat_keys,
        "avg_stats": avg_stats,
        "sorted_tickers": sorted_tickers,
    }


def _format_style_text(style_grid: dict) -> str:
    parts = [
        f"{size}/{val}: {style_grid[(size, val)]:.0f}%"
        for size in ("Large", "Mid", "Small")
        for val in ("Value", "Blend", "Growth")
        if style_grid[(size, val)] > 0
    ]
    return f"Style: {', '.join(parts)}"


def _format_weighted_groups_text(label: str, groups: dict, weight_map: dict) -> str:
    parts = []
    for group, members in groups.items():
        total = sum(weight_map.get(m, 0) for m in members)
        if total > 0:
            detail = ", ".join(
                f"{m} {weight_map[m]:.0f}%" for m in members if weight_map.get(m, 0) > 0
            )
            parts.append(f"{group} {total:.0f}% ({detail})")
    return f"{label}: {'; '.join(parts)}"


def format_xray_text(data: dict) -> str:
    """Format X-Ray data as compact text for LLM context."""
    if not data:
        return "No metadata available."

    profiles = data["profiles"]
    weights = data["weights"]
    avg_stats = data["avg_stats"]
    stat_keys = data["stat_keys"]
    sorted_tickers = data["sorted_tickers"]

    lines = [f"PORTFOLIO X-RAY ({len(profiles)} stocks, equal-weight)"]
    lines.append(_format_style_text(data["style_grid"]))
    lines.append(
        _format_weighted_groups_text("Sectors", SUPERSECTOR_SECTORS, data["sector_wt"])
    )
    lines.append(
        _format_weighted_groups_text("Regions", REGION_SUBREGIONS, data["subregion_wt"])
    )

    stat_parts = [
        f"{label}: {avg_stats[key]:.2f}"
        for key, label in stat_keys.items()
        if avg_stats[key] > 0
    ]
    lines.append(f"Stats: {', '.join(stat_parts)}")

    for ticker in sorted_tickers[:10]:
        p = profiles[ticker]
        mc = p.get("market_capitalization") or 0
        mc_b = f"{mc / 1e9:.0f}B" if mc > 0 else "N/A"
        lines.append(
            f"  ({ticker}) {p.get('name', ticker)} | {p.get('sector', '-')} | {p.get('country', '-')} | MCap {mc_b} | {weights[ticker]:.1f}%"
        )

    return "\n".join(lines)


def format_xray_html(data: dict) -> str:
    """Format X-Ray data as HTML for the final report."""
    if not data:
        return "<h2>X-Ray Analysis</h2><p>No metadata available for the requested tickers.</p>"

    profiles = data["profiles"]
    weights = data["weights"]
    has_allocation = data["has_allocation"]
    style_grid = data["style_grid"]
    sector_wt = data["sector_wt"]
    subregion_wt = data["subregion_wt"]
    avg_stats = data["avg_stats"]
    stat_keys = data["stat_keys"]
    sorted_tickers = data["sorted_tickers"]
    n = len(profiles)

    h = ["<h2>X-Ray Analysis</h2>"]
    if has_allocation:
        h.append(
            f"<p>Weighted breakdown of {n} stocks based on recommended allocation.</p>"
        )
    else:
        h.append(f"<p>Equal-weight breakdown of {n} stocks under analysis.</p>")

    h.extend(_build_style_table(style_grid))
    h.extend(_build_sector_table(sector_wt))
    h.extend(_build_region_table(subregion_wt))
    h.extend(_build_stats_table(stat_keys, avg_stats))
    h.extend(_build_composition_table(sorted_tickers, profiles, weights))

    return "\n".join(h)
