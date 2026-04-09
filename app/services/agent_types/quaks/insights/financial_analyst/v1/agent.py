import json
import re
from datetime import datetime, timedelta

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.constants import START, END
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from typing_extensions import Literal

from app.interface.api.messages.schema import MessageRequest
from app.services.agent_types.base import (
    SupervisedWorkflowAgentBase,
    AgentUtils,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1 import (
    FINANCIAL_ANALYST_V1_AGENTS,
    FINANCIAL_ANALYST_V1_AGENT_CONFIGURATION,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1.prompts import (
    COORDINATOR_SYSTEM_PROMPT,
    DATA_COLLECTOR_SYSTEM_PROMPT,
    FUNDAMENTAL_ANALYST_SYSTEM_PROMPT,
    TECHNICAL_ANALYST_SYSTEM_PROMPT,
    CONSENSUS_REPORTER_SYSTEM_PROMPT,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1.state import FinancialAnalystState
from app.services.agent_types.quaks.insights.tools import build_get_markets_news_tool
from app.services.markets_news import MarketsNewsService
from app.services.markets_stats import MarketsStatsService
from app.services.tasks import TaskProgress

EXECUTION_PLAN = (
    "Financial analysis plan:\n"
    "1. coordinator: Parse ticker(s) and decide whether to proceed\n"
    "2. data_collector: Fetch company profile, price stats, technical indicators, and news for each ticker\n"
    "3. portfolio_xray: Generate Morningstar-style portfolio breakdown (sectors, regions, style, stats)\n"
    "4. fundamental_analyst: Evaluate valuation, profitability, and financial health → BUY/HOLD/SELL\n"
    "5. technical_analyst: Evaluate price action, momentum, and trend signals → BUY/HOLD/SELL\n"
    "6. consensus_reporter: Produce the final HTML report with X-Ray appendix"
)

SUPERSECTOR_SECTORS = {
    "Cyclical": ["Basic Materials", "Consumer Cyclical", "Financial Services", "Real Estate"],
    "Sensitive": ["Communication Services", "Energy", "Industrials", "Technology"],
    "Defensive": ["Consumer Defensive", "Healthcare", "Utilities"],
}

COUNTRY_REGION = {
    "US": ("Americas", "United States"),
    "USA": ("Americas", "United States"),
    "United States": ("Americas", "United States"),
    "Canada": ("Americas", "Canada"),
    "CA": ("Americas", "Canada"),
    "Brazil": ("Americas", "Central & Latin America"),
    "Mexico": ("Americas", "Central & Latin America"),
    "Argentina": ("Americas", "Central & Latin America"),
    "Chile": ("Americas", "Central & Latin America"),
    "Colombia": ("Americas", "Central & Latin America"),
    "Peru": ("Americas", "Central & Latin America"),
    "United Kingdom": ("Greater Europe", "United Kingdom"),
    "Germany": ("Greater Europe", "Western Europe - Euro"),
    "France": ("Greater Europe", "Western Europe - Euro"),
    "Netherlands": ("Greater Europe", "Western Europe - Euro"),
    "Spain": ("Greater Europe", "Western Europe - Euro"),
    "Italy": ("Greater Europe", "Western Europe - Euro"),
    "Belgium": ("Greater Europe", "Western Europe - Euro"),
    "Ireland": ("Greater Europe", "Western Europe - Euro"),
    "Finland": ("Greater Europe", "Western Europe - Euro"),
    "Austria": ("Greater Europe", "Western Europe - Euro"),
    "Portugal": ("Greater Europe", "Western Europe - Euro"),
    "Switzerland": ("Greater Europe", "Western Europe - Non Euro"),
    "Sweden": ("Greater Europe", "Western Europe - Non Euro"),
    "Norway": ("Greater Europe", "Western Europe - Non Euro"),
    "Denmark": ("Greater Europe", "Western Europe - Non Euro"),
    "Poland": ("Greater Europe", "Emerging Europe"),
    "Czech Republic": ("Greater Europe", "Emerging Europe"),
    "Hungary": ("Greater Europe", "Emerging Europe"),
    "Russia": ("Greater Europe", "Emerging Europe"),
    "Turkey": ("Greater Europe", "Emerging Europe"),
    "Israel": ("Greater Europe", "Middle East / Africa"),
    "South Africa": ("Greater Europe", "Middle East / Africa"),
    "Saudi Arabia": ("Greater Europe", "Middle East / Africa"),
    "Japan": ("Greater Asia", "Japan"),
    "Australia": ("Greater Asia", "Australasia"),
    "New Zealand": ("Greater Asia", "Australasia"),
    "Taiwan": ("Greater Asia", "Emerging 4 Tigers"),
    "South Korea": ("Greater Asia", "Emerging 4 Tigers"),
    "Hong Kong": ("Greater Asia", "Emerging 4 Tigers"),
    "Singapore": ("Greater Asia", "Emerging 4 Tigers"),
    "China": ("Greater Asia", "Emerging Asia - Ex 4 Tigers"),
    "India": ("Greater Asia", "Emerging Asia - Ex 4 Tigers"),
    "Indonesia": ("Greater Asia", "Emerging Asia - Ex 4 Tigers"),
    "Malaysia": ("Greater Asia", "Emerging Asia - Ex 4 Tigers"),
    "Thailand": ("Greater Asia", "Emerging Asia - Ex 4 Tigers"),
    "Philippines": ("Greater Asia", "Emerging Asia - Ex 4 Tigers"),
    "Vietnam": ("Greater Asia", "Emerging Asia - Ex 4 Tigers"),
}

REGION_SUBREGIONS = {
    "Americas": ["United States", "Canada", "Central & Latin America"],
    "Greater Europe": [
        "United Kingdom", "Western Europe - Euro", "Western Europe - Non Euro",
        "Emerging Europe", "Middle East / Africa",
    ],
    "Greater Asia": ["Japan", "Australasia", "Emerging 4 Tigers", "Emerging Asia - Ex 4 Tigers"],
}

# Finnhub sector values (from ES metadata) → Morningstar super-sector parent
INDUSTRY_TO_SECTOR = {
    # Technology (Sensitive)
    "Technology": "Technology",
    "Semiconductors": "Technology",
    "Electrical Equipment": "Technology",
    # Communication Services (Sensitive)
    "Media": "Communication Services",
    "Communications": "Communication Services",
    "Telecommunication": "Communication Services",
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
    "Financial Services": "Financial Services",
    "Banking": "Financial Services",
    "Insurance": "Financial Services",
    # Consumer Cyclical (Cyclical)
    "Retail": "Consumer Cyclical",
    "Hotels, Restaurants & Leisure": "Consumer Cyclical",
    "Textiles, Apparel & Luxury Goods": "Consumer Cyclical",
    "Automobiles": "Consumer Cyclical",
    "Auto Components": "Consumer Cyclical",
    "Leisure Products": "Consumer Cyclical",
    "Diversified Consumer Services": "Consumer Cyclical",
    "Consumer products": "Consumer Cyclical",
    # Real Estate (Cyclical)
    "Real Estate": "Real Estate",
    # Basic Materials (Cyclical)
    "Metals & Mining": "Basic Materials",
    "Chemicals": "Basic Materials",
    "Paper & Forest": "Basic Materials",
    # Healthcare (Defensive)
    "Health Care": "Healthcare",
    "Biotechnology": "Healthcare",
    "Pharmaceuticals": "Healthcare",
    "Life Sciences Tools & Services": "Healthcare",
    # Consumer Defensive (Defensive)
    "Food Products": "Consumer Defensive",
    "Beverages": "Consumer Defensive",
    "Tobacco": "Consumer Defensive",
    "Distributors": "Consumer Defensive",
    # Utilities (Defensive)
    "Utilities": "Utilities",
}

# Build lookup of known sector names for fast membership check
_KNOWN_SECTORS = set()
for _sectors in SUPERSECTOR_SECTORS.values():
    _KNOWN_SECTORS.update(_sectors)

# Keyword hints for fuzzy fallback when exact match fails
_SECTOR_KEYWORDS = {
    "Technology": ["tech", "software", "semiconductor", "computer", "electronic", "solar", "cyber"],
    "Communication Services": ["media", "telecom", "entertainment", "gaming", "advertis", "broadcast", "publish", "streaming"],
    "Healthcare": ["health", "drug", "biotech", "medical", "pharma", "diagnostic"],
    "Financial Services": ["bank", "insurance", "capital", "credit", "asset management", "financial"],
    "Consumer Cyclical": ["retail", "auto", "restaurant", "apparel", "luxury", "travel", "hotel", "leisure"],
    "Consumer Defensive": ["food", "beverage", "grocery", "tobacco", "household", "discount"],
    "Industrials": ["aerospace", "defense", "railroad", "airline", "freight", "waste", "construction", "industrial"],
    "Energy": ["oil", "gas", "energy", "petroleum", "fuel"],
    "Utilities": ["utilit", "electric", "water", "renewable"],
    "Real Estate": ["reit", "real estate", "property"],
    "Basic Materials": ["gold", "steel", "chemical", "copper", "mining", "lumber", "aluminum"],
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
    return "Not Classified"


def _build_style_table(style_grid: dict) -> list[str]:
    rows = ["<h3>Investment Style</h3>", "<table>",
            "<tr><th></th><th>Value</th><th>Blend</th><th>Growth</th></tr>"]
    for size in ("Large", "Mid", "Small"):
        v, b, g = [f"{style_grid[(size, st)]:.0f}" for st in ("Value", "Blend", "Growth")]
        rows.append(f"<tr><td><b>{size}</b></td><td>{v}</td><td>{b}</td><td>{g}</td></tr>")
    rows.append("</table>")
    return rows


def _build_sector_table(sector_wt: dict) -> list[str]:
    rows = ["<h3>Stock Sectors</h3>", "<table>",
            "<tr><th>Sector</th><th>Weight %</th></tr>"]
    for supersector, sectors in SUPERSECTOR_SECTORS.items():
        total = sum(sector_wt.get(s, 0) for s in sectors)
        rows.append(f"<tr><td><b>{supersector}</b></td><td><b>{total:.2f}</b></td></tr>")
        for s in sectors:
            w = sector_wt.get(s, 0)
            if w > 0:
                rows.append(f"<tr><td>&nbsp;&nbsp;{s}</td><td>{w:.2f}</td></tr>")
    nc = sector_wt.get("Not Classified", 0)
    if nc > 0:
        rows.append(f"<tr><td><b>Not Classified</b></td><td><b>{nc:.2f}</b></td></tr>")
    rows.append("</table>")
    return rows


def _build_region_table(subregion_wt: dict) -> list[str]:
    rows = ["<h3>World Regions</h3>", "<table>",
            "<tr><th>Region</th><th>Weight %</th></tr>"]
    for region, subregions in REGION_SUBREGIONS.items():
        total = sum(subregion_wt.get(sr, 0) for sr in subregions)
        if total > 0:
            rows.append(f"<tr><td><b>{region}</b></td><td><b>{total:.2f}</b></td></tr>")
            for sr in subregions:
                w = subregion_wt.get(sr, 0)
                if w > 0:
                    rows.append(f"<tr><td>&nbsp;&nbsp;{sr}</td><td>{w:.2f}</td></tr>")
    nc = subregion_wt.get("Not Classified", 0)
    if nc > 0:
        rows.append(f"<tr><td><b>Not Classified</b></td><td><b>{nc:.2f}</b></td></tr>")
    rows.append("</table>")
    return rows


def _build_stats_table(stat_keys: dict, avg_stats: dict) -> list[str]:
    rows = ["<h3>Stock Stats</h3>", "<table>",
            "<tr><th>Metric</th><th>Average</th></tr>"]
    for key, label in stat_keys.items():
        val = f"{avg_stats[key]:.2f}" if avg_stats[key] > 0 else "-"
        rows.append(f"<tr><td>{label}</td><td>{val}</td></tr>")
    rows.append("</table>")
    return rows


def _build_composition_table(sorted_tickers: list, profiles: dict, weights: dict) -> list[str]:
    rows = ["<h3>Composition</h3>", "<table>",
            "<tr><th>Name</th><th>Ticker</th><th>Sector</th><th>Country</th><th>Weight %</th></tr>"]
    for ticker in sorted_tickers[:10]:
        p = profiles[ticker]
        rows.append(
            f"<tr><td>{p.get('name', ticker)}</td><td>({ticker})</td>"
            f"<td>{p.get('sector', '-')}</td><td>{p.get('country', '-')}</td>"
            f"<td>{weights[ticker]:.2f}</td></tr>"
        )
    rows.append("</table>")
    return rows


class QuaksFinancialAnalystV1Agent(SupervisedWorkflowAgentBase):
    def __init__(
        self,
        agent_utils: AgentUtils,
        markets_stats_service: MarketsStatsService,
        markets_news_service: MarketsNewsService,
    ):
        super().__init__(agent_utils)
        self.markets_stats_service = markets_stats_service
        self.markets_news_service = markets_news_service

    def create_default_settings(self, agent_id: str, schema: str):
        prompts = {
            "coordinator_system_prompt": COORDINATOR_SYSTEM_PROMPT,
            "data_collector_system_prompt": DATA_COLLECTOR_SYSTEM_PROMPT,
            "fundamental_analyst_system_prompt": FUNDAMENTAL_ANALYST_SYSTEM_PROMPT,
            "technical_analyst_system_prompt": TECHNICAL_ANALYST_SYSTEM_PROMPT,
            "consensus_reporter_system_prompt": CONSENSUS_REPORTER_SYSTEM_PROMPT,
        }
        for key, value in prompts.items():
            self.agent_setting_service.create_agent_setting(
                agent_id=agent_id,
                setting_key=key,
                setting_value=value,
                schema=schema,
            )

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(FinancialAnalystState)
        workflow_builder.add_edge(START, "coordinator")
        workflow_builder.add_node("coordinator", self.get_coordinator)
        workflow_builder.add_node("data_collector", self.get_data_collector)
        workflow_builder.add_node("fundamental_analyst", self.get_fundamental_analyst)
        workflow_builder.add_node("technical_analyst", self.get_technical_analyst)
        workflow_builder.add_node("consensus_reporter", self.get_consensus_reporter)
        workflow_builder.add_node("portfolio_xray", self.get_portfolio_xray)
        workflow_builder.add_edge("data_collector", "portfolio_xray")
        workflow_builder.add_edge("portfolio_xray", "fundamental_analyst")
        workflow_builder.add_edge("fundamental_analyst", "technical_analyst")
        workflow_builder.add_edge("technical_analyst", "consensus_reporter")
        workflow_builder.add_edge("consensus_reporter", END)
        return workflow_builder

    def get_input_params(self, message_request: MessageRequest, schema: str) -> dict:
        settings = self.agent_setting_service.get_agent_settings(
            message_request.agent_id, schema
        )
        settings_dict = {
            setting.setting_key: setting.setting_value for setting in settings
        }

        tickers = self._parse_tickers(message_request.message_content)

        template_vars = {
            "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
            "EXECUTION_PLAN": EXECUTION_PLAN,
            "TICKERS": ", ".join(tickers) if tickers else "To be determined from user query",
            "FINANCIAL_ANALYST_AGENTS": FINANCIAL_ANALYST_V1_AGENTS,
            "FINANCIAL_ANALYST_AGENT_CONFIGURATION": FINANCIAL_ANALYST_V1_AGENT_CONFIGURATION,
        }

        return {
            "agent_id": message_request.agent_id,
            "schema": schema,
            "query": message_request.message_content,
            "tickers": tickers,
            "execution_plan": EXECUTION_PLAN,
            "coordinator_system_prompt": self.parse_prompt_template(
                settings_dict, "coordinator_system_prompt", template_vars
            ),
            "data_collector_system_prompt": self.parse_prompt_template(
                settings_dict, "data_collector_system_prompt", template_vars
            ),
            "fundamental_analyst_system_prompt": self.parse_prompt_template(
                settings_dict, "fundamental_analyst_system_prompt", template_vars
            ),
            "technical_analyst_system_prompt": self.parse_prompt_template(
                settings_dict, "technical_analyst_system_prompt", template_vars
            ),
            "consensus_reporter_system_prompt": self.parse_prompt_template(
                settings_dict, "consensus_reporter_system_prompt", template_vars
            ),
            "fundamental_recommendation": "",
            "technical_recommendation": "",
            "consensus_verdict": "",
            "allocation_weights": "",
            "portfolio_xray_html": "",
            "messages": [HumanMessage(content=message_request.message_content)],
        }

    @staticmethod
    def _parse_tickers(message_content: str) -> list[str]:
        """Extract ticker symbols from BATCH_ETL messages only.

        Only BATCH_ETL triggers the full analysis pipeline.
        Supports: BATCH_ETL AAPL MSFT, BATCH_ETL AAPL,MSFT,NVDA
        """
        content = message_content.strip()
        if not content.startswith("BATCH_ETL"):
            return []
        content = content.replace("BATCH_ETL", "").strip()
        tokens = re.split(r"[,\s]+", content)
        tickers = [t.upper() for t in tokens if re.match(r"^[A-Z]{1,5}$", t.upper())]
        return tickers

    def _build_tools(self):
        markets_stats_service = self.markets_stats_service
        markets_news_service = self.markets_news_service

        @tool("fetch_company_profile")
        def fetch_company_profile(ticker: str) -> str:
            """Fetch company metadata, valuation multiples, analyst ratings, and ownership data.

            Args:
                ticker: Stock ticker symbol (e.g. AAPL, MSFT, NVDA).

            Returns:
                JSON string with company profile data.
            """
            result = markets_stats_service.get_company_profile(
                index_name="quaks_stocks-metadata_latest",
                key_ticker=ticker,
            )
            return json.dumps(result, ensure_ascii=False, default=str)

        @tool("fetch_stats_close")
        def fetch_stats_close(ticker: str) -> str:
            """Fetch latest price stats including OHLCV and percent variance for a ticker.

            Args:
                ticker: Stock ticker symbol (e.g. AAPL, MSFT, NVDA).

            Returns:
                JSON string with price stats.
            """
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            result = markets_stats_service.get_stats_close(
                index_name="quaks_stocks-eod_latest",
                key_ticker=ticker,
                start_date=start_date,
                end_date=end_date,
            )
            return json.dumps(result, ensure_ascii=False, default=str)

        @tool("fetch_technical_indicators")
        def fetch_technical_indicators(ticker: str) -> str:
            """Fetch technical indicators (RSI, MACD, EMA, ADX) for a ticker.

            Args:
                ticker: Stock ticker symbol (e.g. AAPL, MSFT, NVDA).

            Returns:
                JSON string with technical indicator values.
            """
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            indicators = {
                "rsi": markets_stats_service.get_indicator_rsi(
                    index_name="quaks_stocks-eod_latest",
                    key_ticker=ticker,
                    start_date=start_date,
                    end_date=end_date,
                    period=14,
                ),
                "macd": markets_stats_service.get_indicator_macd(
                    index_name="quaks_stocks-eod_latest",
                    key_ticker=ticker,
                    start_date=start_date,
                    end_date=end_date,
                    short_window=12,
                    long_window=26,
                    signal_window=9,
                ),
                "ema": markets_stats_service.get_indicator_ema(
                    index_name="quaks_stocks-eod_latest",
                    key_ticker=ticker,
                    start_date=start_date,
                    end_date=end_date,
                    short_window=10,
                    long_window=20,
                ),
                "adx": markets_stats_service.get_indicator_adx(
                    index_name="quaks_stocks-eod_latest",
                    key_ticker=ticker,
                    start_date=start_date,
                    end_date=end_date,
                    period=14,
                ),
            }
            return json.dumps(indicators, ensure_ascii=False, default=str)

        return [fetch_company_profile, fetch_stats_close, fetch_technical_indicators, build_get_markets_news_tool(markets_news_service), self._build_xray_tool()]

    def _build_xray_tool(self):
        compute_data = self._compute_xray_data
        format_text = self._format_xray_text

        @tool("fetch_portfolio_xray")
        def fetch_portfolio_xray(tickers: str) -> str:
            """Generate an X-Ray analysis for a combination of stock tickers.

            Provides Morningstar-style breakdown including investment style box,
            sector classification, geographic exposure, valuation stats,
            and composition details. Uses equal weighting across all tickers.

            Args:
                tickers: Comma-separated ticker symbols (e.g. "AAPL,MSFT,NVDA").

            Returns:
                Text summary of the X-Ray analysis.
            """
            ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
            data = compute_data(ticker_list)
            return format_text(data)

        return fetch_portfolio_xray

    def _compute_xray_data(self, tickers: list[str], allocation: dict = None) -> dict:
        """Compute X-Ray structured data from ticker metadata. Deterministic — no LLM."""
        profiles = {}
        for ticker in tickers:
            profile = self.markets_stats_service.get_company_profile(
                index_name="quaks_stocks-metadata_latest",
                key_ticker=ticker,
            )
            if profile:
                profiles[ticker] = profile

        if not profiles:
            return {}

        n = len(profiles)
        weights, has_allocation = self._compute_weights(profiles, allocation, n)

        style_grid = {(s, v): 0.0 for s in ("Large", "Mid", "Small") for v in ("Value", "Blend", "Growth")}
        for ticker, p in profiles.items():
            mc = p.get("market_capitalization") or 0
            pe = p.get("forward_pe") or p.get("pe_ratio") or 0
            style_grid[(_classify_size(mc), _classify_style(pe))] += weights[ticker]

        sector_wt = {}
        for ticker, p in profiles.items():
            raw = p.get("sector") or "Not Classified"
            s = _normalize_sector(raw)
            sector_wt[s] = sector_wt.get(s, 0) + weights[ticker]

        subregion_wt = {}
        for ticker, p in profiles.items():
            c = p.get("country") or "Not Classified"
            _, sr = COUNTRY_REGION.get(c, ("Not Classified", "Not Classified"))
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
        avg_stats = self._compute_avg_stats(profiles, weights, stat_keys)

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

    @staticmethod
    def _compute_weights(profiles, allocation, n):
        if allocation:
            raw_wt = {t: allocation.get(t, 0) for t in profiles}
            total = sum(raw_wt.values())
            weights = {t: w * 100.0 / total for t, w in raw_wt.items()} if total > 0 else {t: 100.0 / n for t in profiles}
            return weights, True
        return {t: 100.0 / n for t in profiles}, False

    @staticmethod
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

    @staticmethod
    def _format_xray_text(data: dict) -> str:
        """Format X-Ray data as compact text for LLM context."""
        if not data:
            return "No metadata available."

        profiles = data["profiles"]
        weights = data["weights"]
        style_grid = data["style_grid"]
        sector_wt = data["sector_wt"]
        subregion_wt = data["subregion_wt"]
        avg_stats = data["avg_stats"]
        stat_keys = data["stat_keys"]
        sorted_tickers = data["sorted_tickers"]

        lines = [f"PORTFOLIO X-RAY ({len(profiles)} stocks, equal-weight)"]

        # Style box — only non-zero cells
        style_parts = []
        for size in ("Large", "Mid", "Small"):
            for val_style in ("Value", "Blend", "Growth"):
                w = style_grid[(size, val_style)]
                if w > 0:
                    style_parts.append(f"{size}/{val_style}: {w:.0f}%")
        lines.append(f"Style: {', '.join(style_parts)}")

        # Sectors — only non-zero
        sector_parts = []
        for supersector, sectors in SUPERSECTOR_SECTORS.items():
            total = sum(sector_wt.get(s, 0) for s in sectors)
            if total > 0:
                detail = ", ".join(f"{s} {sector_wt[s]:.0f}%" for s in sectors if sector_wt.get(s, 0) > 0)
                sector_parts.append(f"{supersector} {total:.0f}% ({detail})")
        lines.append(f"Sectors: {'; '.join(sector_parts)}")

        # Regions — only non-zero
        region_parts = []
        for region, subregions in REGION_SUBREGIONS.items():
            total = sum(subregion_wt.get(sr, 0) for sr in subregions)
            if total > 0:
                detail = ", ".join(f"{sr} {subregion_wt[sr]:.0f}%" for sr in subregions if subregion_wt.get(sr, 0) > 0)
                region_parts.append(f"{region} {total:.0f}% ({detail})")
        lines.append(f"Regions: {'; '.join(region_parts)}")

        # Stats — only non-zero
        stat_parts = [f"{label}: {avg_stats[key]:.2f}" for key, label in stat_keys.items() if avg_stats[key] > 0]
        lines.append(f"Stats: {', '.join(stat_parts)}")

        # Composition — one line per ticker
        for ticker in sorted_tickers[:10]:
            p = profiles[ticker]
            mc = p.get("market_capitalization") or 0
            mc_b = f"{mc / 1e9:.0f}B" if mc > 0 else "N/A"
            lines.append(f"  ({ticker}) {p.get('name', ticker)} | {p.get('sector', '-')} | {p.get('country', '-')} | MCap {mc_b} | {weights[ticker]:.1f}%")

        return "\n".join(lines)

    @staticmethod
    def _format_xray_html(data: dict) -> str:
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
            h.append(f"<p>Weighted breakdown of {n} stocks based on recommended allocation.</p>")
        else:
            h.append(f"<p>Equal-weight breakdown of {n} stocks under analysis.</p>")

        h.extend(_build_style_table(style_grid))
        h.extend(_build_sector_table(sector_wt))
        h.extend(_build_region_table(subregion_wt))
        h.extend(_build_stats_table(stat_keys, avg_stats))
        h.extend(_build_composition_table(sorted_tickers, profiles, weights))

        return "\n".join(h)

    def _invoke_chain(self, agent_id, schema, system_prompt, messages):
        """Invoke a simple system+messages chain and return a single AIMessage."""
        chat_model = self.get_chat_model(agent_id, schema)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("placeholder", "{messages}"),
            ]
        )
        chain = prompt | chat_model
        response = chain.invoke({"messages": messages})
        return response

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        """Remove markdown code fences and inline formatting from LLM output."""
        # Remove ```html ... ``` wrappers
        text = re.sub(r"^```\w*\n?", "", text.strip())
        text = re.sub(r"\n?```$", "", text.strip())
        # Remove inline markdown: *text*, **text**, _text_, __text__
        text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
        text = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", text)
        return text.strip()

    @staticmethod
    def _get_last_named_message(messages, name):
        """Return the last message with the given name, or None."""
        for msg in reversed(messages):
            if getattr(msg, "name", None) == name:
                return msg
        return None

    def get_coordinator(
        self, state: FinancialAnalystState
    ) -> Command[Literal["data_collector", "__end__"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]
        query = state["query"]
        tickers = state["tickers"]

        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> Query -> {query}")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content=f"Analyzing query: {query}",
            )
        )

        is_batch = query.strip().startswith("BATCH_ETL")

        if tickers:
            self.logger.info(f"Agent[{agent_id}] -> Coordinator -> Tickers: {tickers} -> data_collector")
            return Command(
                goto="data_collector",
                update={"messages": [AIMessage(
                    content=f"Proceeding with financial analysis for: {', '.join(tickers)}",
                    name="coordinator",
                )]},
            )

        if is_batch:
            self.logger.info(f"Agent[{agent_id}] -> Coordinator -> BATCH_ETL without tickers")
            return Command(
                goto=END,
                update={"messages": [AIMessage(
                    content="BATCH_ETL requires ticker symbols. Example: BATCH_ETL AAPL,MSFT,NVDA",
                    name="coordinator",
                )]},
            )

        # QA mode: answer directly, with portfolio X-ray tool available
        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> QA mode")
        chat_model = self.get_chat_model(agent_id, schema)
        coordinator = create_react_agent(
            model=chat_model,
            tools=[self._build_xray_tool()],
            prompt=state["coordinator_system_prompt"],
        )
        response = coordinator.invoke(state)
        return Command(
            goto=END,
            update={"messages": response["messages"]},
        )

    def get_data_collector(self, state: FinancialAnalystState) -> Command[Literal["fundamental_analyst"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]

        tickers_str = ", ".join(state["tickers"])
        self.logger.info(f"Agent[{agent_id}] -> Data Collector -> {tickers_str}")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content=f"Collecting financial data for {tickers_str}...",
            )
        )

        chat_model = self.get_chat_model(agent_id, schema)
        data_collector = create_react_agent(
            model=chat_model,
            tools=self._build_tools(),
            prompt=state["data_collector_system_prompt"],
        )
        response = data_collector.invoke(state)

        # Extract the final summary (last AI message) from the react agent
        collected_data = response["messages"][-1].content if response["messages"] else ""

        self.logger.info(f"Agent[{agent_id}] -> Data Collector -> Complete")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Financial data collected.",
            )
        )
        return Command(
            update={"messages": [AIMessage(content=collected_data, name="data_collector")]},
            goto="fundamental_analyst",
        )

    def get_fundamental_analyst(self, state: FinancialAnalystState) -> Command[Literal["technical_analyst"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]

        self.logger.info(f"Agent[{agent_id}] -> Fundamental Analyst")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Running fundamental analysis...",
            )
        )

        # Pass collected data + X-Ray text context
        data_msg = self._get_last_named_message(state["messages"], "data_collector")
        xray_msg = self._get_last_named_message(state["messages"], "portfolio_xray")
        data_content = data_msg.content if data_msg else ""
        if xray_msg:
            data_content += f"\n\n{xray_msg.content}"
        messages = [HumanMessage(content=data_content)]

        response = self._invoke_chain(
            agent_id, schema, state["fundamental_analyst_system_prompt"], messages
        )

        self.logger.info(f"Agent[{agent_id}] -> Fundamental Analyst -> Complete")
        return Command(
            update={
                "messages": [AIMessage(content=response.content, name="fundamental_analyst")],
                "fundamental_recommendation": response.content,
            },
            goto="technical_analyst",
        )

    def get_technical_analyst(self, state: FinancialAnalystState) -> Command[Literal["consensus_reporter"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]

        self.logger.info(f"Agent[{agent_id}] -> Technical Analyst")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Running technical analysis...",
            )
        )

        # Pass collected data + X-Ray text context
        data_msg = self._get_last_named_message(state["messages"], "data_collector")
        xray_msg = self._get_last_named_message(state["messages"], "portfolio_xray")
        data_content = data_msg.content if data_msg else ""
        if xray_msg:
            data_content += f"\n\n{xray_msg.content}"
        messages = [HumanMessage(content=data_content)]

        response = self._invoke_chain(
            agent_id, schema, state["technical_analyst_system_prompt"], messages
        )

        self.logger.info(f"Agent[{agent_id}] -> Technical Analyst -> Complete")
        return Command(
            update={
                "messages": [AIMessage(content=response.content, name="technical_analyst")],
                "technical_recommendation": response.content,
            },
            goto="consensus_reporter",
        )

    @staticmethod
    def _extract_executive_summary(html: str) -> str:
        match = re.search(r"<blockquote>(.*?)</blockquote>", html, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_allocation(html: str) -> dict:
        """Extract allocation weights from ALLOCATION: TICKER=XX,... in report HTML."""
        match = re.search(r"ALLOCATION:\s*([\w=,.\s()]+)", html)
        if not match:
            return {}
        weights = {}
        for pair in match.group(1).strip().split(","):
            pair = pair.strip()
            if "=" in pair:
                ticker, pct = pair.split("=", 1)
                # Strip parentheses in case LLM wraps ticker as (SYMBOL)
                ticker = ticker.strip().strip("()")
                try:
                    weights[ticker] = float(pct.strip().strip("()"))
                except ValueError:
                    continue
        return weights

    def get_consensus_reporter(self, state: FinancialAnalystState):
        agent_id = state["agent_id"]
        schema = state["schema"]

        self.logger.info(f"Agent[{agent_id}] -> Consensus Reporter")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Building consensus and formatting final report...",
            )
        )

        # Pass analyst recommendations + X-Ray text — stripped of markdown
        fundamental = self._strip_markdown_fences(state["fundamental_recommendation"])
        technical = self._strip_markdown_fences(state["technical_recommendation"])
        xray_msg = self._get_last_named_message(state["messages"], "portfolio_xray")
        input_parts = [
            f"FUNDAMENTAL ANALYSIS:\n{fundamental}",
            f"TECHNICAL ANALYSIS:\n{technical}",
        ]
        if xray_msg:
            input_parts.append(xray_msg.content)
        messages = [HumanMessage(content="\n\n".join(input_parts))]

        response = self._invoke_chain(
            agent_id, schema, state["consensus_reporter_system_prompt"], messages
        )

        report_html = self._strip_markdown_fences(response.content)
        executive_summary = self._extract_executive_summary(report_html)
        allocation = self._extract_allocation(report_html)

        self.logger.info(f"Agent[{agent_id}] -> Consensus Reporter -> Complete")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content=executive_summary[:200] if executive_summary else report_html[:200],
            )
        )
        return {
            "messages": [AIMessage(content=report_html, name="consensus_reporter")],
            "consensus_verdict": report_html,
            "executive_summary": executive_summary,
            "allocation_weights": json.dumps(allocation) if allocation else "",
        }

    def get_portfolio_xray(self, state: FinancialAnalystState):
        agent_id = state["agent_id"]
        tickers = state["tickers"]

        if not tickers:
            return {"portfolio_xray_html": ""}

        self.logger.info(f"Agent[{agent_id}] -> Portfolio X-Ray")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Generating Portfolio X-Ray...",
            )
        )

        # Runs before analysts — always equal-weight at this stage
        xray_data = self._compute_xray_data(tickers)
        xray_html = self._format_xray_html(xray_data)
        xray_text = self._format_xray_text(xray_data)

        self.logger.info(f"Agent[{agent_id}] -> Portfolio X-Ray -> Complete")
        return {
            "portfolio_xray_html": xray_html,
            "messages": [AIMessage(content=xray_text, name="portfolio_xray")],
        }

    def format_response(self, workflow_state: MessagesState) -> (str, dict):
        consensus_html = workflow_state.get("consensus_verdict", "")
        xray_html = workflow_state.get("portfolio_xray_html", "")
        executive_summary = workflow_state.get("executive_summary", "")

        if consensus_html:
            # Batch mode: X-Ray first, then consensus report
            if xray_html:
                report_html = xray_html + "\n<hr>\n" + consensus_html
            else:
                report_html = consensus_html
        else:
            # QA mode: use last message content
            report_html = workflow_state["messages"][-1].content

        response_data = {
            "executive_summary": executive_summary,
            "report_html": report_html,
            "fundamental_recommendation": workflow_state.get("fundamental_recommendation", ""),
            "technical_recommendation": workflow_state.get("technical_recommendation", ""),
            "consensus_verdict": consensus_html,
            "allocation_weights": workflow_state.get("allocation_weights", ""),
            "portfolio_xray_html": xray_html,
            "messages": [
                json.loads(message.model_dump_json())
                for message in workflow_state["messages"]
            ],
        }
        return report_html, response_data

    # --- Abstract method stubs (not used — graph uses deterministic edges) ---

    def get_planner(self, state: FinancialAnalystState) -> Command[Literal["supervisor"]]:
        return Command(goto="supervisor")

    def get_supervisor(self, state: FinancialAnalystState) -> Command:
        return Command(goto=END)

    def get_reporter(self, state: FinancialAnalystState) -> Command[Literal["supervisor"]]:
        return Command(goto="supervisor")
