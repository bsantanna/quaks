from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Annotated, Optional

from fastmcp import FastMCP
from jinja2.sandbox import SandboxedEnvironment
from pydantic import Field

from app.interface.mcp.registrar import McpRegistrar
from app.interface.mcp.user_prompt_resolver import UserPromptResolver
from app.services.agent_types.quaks.insights.financial_analyst.v1.portfolio_xray import (
    compute_xray_data,
    format_xray_text,
)
from app.services.agent_types.quaks.insights.financial_analyst.v1.prompts import (
    CONSENSUS_REPORTER_SYSTEM_PROMPT,
    COORDINATOR_SYSTEM_PROMPT,
    DATA_COLLECTOR_SYSTEM_PROMPT,
    EXECUTION_PLAN,
    FUNDAMENTAL_ANALYST_SYSTEM_PROMPT,
    TECHNICAL_ANALYST_SYSTEM_PROMPT,
)

if TYPE_CHECKING:
    from app.core.container import Container

_AGENT_TYPE = "quaks_financial_analyst_v1"

_DEFAULT_TICKERS = "To be determined from user query"

_ROLE_SETTING_KEYS = {
    "coordinator": "coordinator_system_prompt",
    "data_collector": "data_collector_system_prompt",
    "fundamental_analyst": "fundamental_analyst_system_prompt",
    "technical_analyst": "technical_analyst_system_prompt",
    "consensus_reporter": "consensus_reporter_system_prompt",
}

_DEFAULT_TEMPLATES = {
    "coordinator": COORDINATOR_SYSTEM_PROMPT,
    "data_collector": DATA_COLLECTOR_SYSTEM_PROMPT,
    "fundamental_analyst": FUNDAMENTAL_ANALYST_SYSTEM_PROMPT,
    "technical_analyst": TECHNICAL_ANALYST_SYSTEM_PROMPT,
    "consensus_reporter": CONSENSUS_REPORTER_SYSTEM_PROMPT,
}


_JINJA_ENV = SandboxedEnvironment()


def _render_prompt(
    template_str: str,
    current_time: str | None = None,
    tickers: str | None = None,
) -> str:
    if current_time is not None and not current_time.strip():
        raise ValueError("current_time must be a non-empty string when provided")
    if tickers is not None and not tickers.strip():
        raise ValueError("tickers must be a non-empty string when provided")
    template = _JINJA_ENV.from_string(template_str)
    resolved_time = current_time or datetime.now().strftime("%a %b %d %Y %H:%M:%S %z")
    resolved_tickers = tickers or _DEFAULT_TICKERS
    return template.render(
        CURRENT_TIME=resolved_time,
        EXECUTION_PLAN=EXECUTION_PLAN,
        TICKERS=resolved_tickers,
    )


class FinancialAnalystV1ToolRegistrar(McpRegistrar):
    """Registers MCP tools, prompts, and resources for the quaks_financial_analyst_v1 agent."""

    def __init__(self, user_prompt_resolver: UserPromptResolver) -> None:
        self._user_prompt_resolver = user_prompt_resolver

    def _resolve_prompt(
        self,
        role: str,
        current_time: str | None = None,
        tickers: str | None = None,
    ) -> str:
        return self._user_prompt_resolver.resolve(
            agent_type=_AGENT_TYPE,
            setting_key=_ROLE_SETTING_KEYS[role],
            default_template=_DEFAULT_TEMPLATES[role],
            render=lambda t: _render_prompt(
                t, current_time=current_time, tickers=tickers
            ),
        )

    def register_tools(self, mcp: FastMCP, container: Container) -> None:
        @mcp.tool(
            name="fetch_company_profile_mcp",
            description="Fetch company metadata, valuation multiples "
            "(P/E, forward P/E, P/B, P/S), profitability (margins, ROE, ROA), "
            "growth rates, analyst ratings, dividend yield, market cap, beta, "
            "52-week high/low, sector, country, and ownership data for a single "
            "stock ticker. Source: Elasticsearch metadata index.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def fetch_company_profile_mcp(
            ticker: Annotated[
                str,
                Field(description="Stock ticker symbol (e.g. 'AAPL', 'MSFT', 'NVDA')"),
            ],
        ) -> dict:
            svc = container.markets_stats_service()
            return svc.get_company_profile(
                index_name="quaks_stocks-metadata_latest",
                key_ticker=ticker.upper(),
            )

        @mcp.tool(
            name="fetch_stats_close_mcp",
            description="Fetch latest OHLCV price stats and percent variance over "
            "a date range for a single stock ticker. Defaults to the last 365 days. "
            "Source: Elasticsearch EOD index.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def fetch_stats_close_mcp(
            ticker: Annotated[
                str,
                Field(description="Stock ticker symbol (e.g. 'AAPL', 'MSFT', 'NVDA')"),
            ],
            start_date: Annotated[
                Optional[str],
                Field(
                    description="Start date in yyyy-mm-dd format. Defaults to 365 days ago."
                ),
            ] = None,
            end_date: Annotated[
                Optional[str],
                Field(description="End date in yyyy-mm-dd format. Defaults to today."),
            ] = None,
        ) -> dict:
            svc = container.markets_stats_service()
            resolved_end = end_date or datetime.now().strftime("%Y-%m-%d")
            resolved_start = start_date or (
                datetime.now() - timedelta(days=365)
            ).strftime("%Y-%m-%d")
            return svc.get_stats_close(
                index_name="quaks_stocks-eod_latest",
                key_ticker=ticker.upper(),
                start_date=resolved_start,
                end_date=resolved_end,
            )

        @mcp.tool(
            name="fetch_technical_indicators_mcp",
            description="Fetch technical indicators (RSI-14, MACD 12/26/9, "
            "EMA 10/20 crossover, ADX-14) for a single stock ticker over "
            "a date range. Defaults to the last 365 days. "
            "Source: Elasticsearch EOD index.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def fetch_technical_indicators_mcp(
            ticker: Annotated[
                str,
                Field(description="Stock ticker symbol (e.g. 'AAPL', 'MSFT', 'NVDA')"),
            ],
            start_date: Annotated[
                Optional[str],
                Field(
                    description="Start date in yyyy-mm-dd format. Defaults to 365 days ago."
                ),
            ] = None,
            end_date: Annotated[
                Optional[str],
                Field(description="End date in yyyy-mm-dd format. Defaults to today."),
            ] = None,
        ) -> dict:
            svc = container.markets_stats_service()
            resolved_end = end_date or datetime.now().strftime("%Y-%m-%d")
            resolved_start = start_date or (
                datetime.now() - timedelta(days=365)
            ).strftime("%Y-%m-%d")
            index_name = "quaks_stocks-eod_latest"
            key = ticker.upper()
            return {
                "rsi": svc.get_indicator_rsi(
                    index_name=index_name,
                    key_ticker=key,
                    start_date=resolved_start,
                    end_date=resolved_end,
                    period=14,
                ),
                "macd": svc.get_indicator_macd(
                    index_name=index_name,
                    key_ticker=key,
                    start_date=resolved_start,
                    end_date=resolved_end,
                    short_window=12,
                    long_window=26,
                    signal_window=9,
                ),
                "ema": svc.get_indicator_ema(
                    index_name=index_name,
                    key_ticker=key,
                    start_date=resolved_start,
                    end_date=resolved_end,
                    short_window=10,
                    long_window=20,
                ),
                "adx": svc.get_indicator_adx(
                    index_name=index_name,
                    key_ticker=key,
                    start_date=resolved_start,
                    end_date=resolved_end,
                    period=14,
                ),
            }

        @mcp.tool(
            name="fetch_portfolio_xray_mcp",
            description="Generate a Morningstar-style Portfolio X-Ray for a list "
            "of stock tickers: investment style box (size x value/growth), sector "
            "breakdown (Cyclical/Sensitive/Defensive), world region exposure, "
            "weighted-average stats (P/E, P/B, margins, ROE, beta), and top holdings. "
            "Uses equal weighting across tickers. Returns a compact text summary.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def fetch_portfolio_xray_mcp(
            tickers: Annotated[
                str,
                Field(
                    description="Comma-separated stock ticker symbols (e.g. 'AAPL,MSFT,NVDA')"
                ),
            ],
        ) -> str:
            svc = container.markets_stats_service()
            ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
            data = compute_xray_data(svc, ticker_list)
            return format_xray_text(data)

    def register_prompts(self, mcp: FastMCP) -> None:
        @mcp.prompt(
            name="financial_analyst_v1_coordinator",
            description="System prompt for the Financial Analyst coordinator step. "
            "Answers investment and financial analysis questions directly, or routes "
            "batch requests (prefixed 'BATCH_ETL') to the data collector for full "
            "multi-ticker analysis. Returns a ready-to-use system prompt.",
        )
        def financial_analyst_v1_coordinator(
            current_time: Annotated[
                Optional[str],
                Field(
                    description="Current timestamp to embed in the prompt (e.g. 'Mon Apr 06 2026 18:46:44'). Defaults to server time."
                ),
            ] = None,
            tickers: Annotated[
                Optional[str],
                Field(
                    description="Comma-separated tickers under analysis (e.g. 'AAPL,MSFT'). Defaults to a placeholder."
                ),
            ] = None,
        ) -> str:
            return self._resolve_prompt(
                "coordinator", current_time=current_time, tickers=tickers
            )

        @mcp.prompt(
            name="financial_analyst_v1_data_collector",
            description="System prompt for the Financial Analyst data collector step. "
            "Instructs the LLM to fetch company profile, price stats, technical "
            "indicators, and news for each ticker using the "
            "fetch_company_profile_mcp, fetch_stats_close_mcp, "
            "fetch_technical_indicators_mcp, and get_markets_news_mcp tools. "
            "Returns a ready-to-use system prompt with current timestamp, execution plan, and tickers.",
        )
        def financial_analyst_v1_data_collector(
            current_time: Annotated[
                Optional[str],
                Field(
                    description="Current timestamp to embed in the prompt. Defaults to server time."
                ),
            ] = None,
            tickers: Annotated[
                Optional[str],
                Field(
                    description="Comma-separated tickers under analysis (e.g. 'AAPL,MSFT')."
                ),
            ] = None,
        ) -> str:
            return self._resolve_prompt(
                "data_collector", current_time=current_time, tickers=tickers
            )

        @mcp.prompt(
            name="financial_analyst_v1_fundamental_analyst",
            description="System prompt for the Financial Analyst fundamental analyst step. "
            "Performs chain-of-thought valuation analysis: multiples (P/E, forward P/E, "
            "P/B), profitability (margins, ROE), growth, risk profile. Produces a "
            "BUY/HOLD/SELL recommendation with a conviction score (1-10) per ticker.",
        )
        def financial_analyst_v1_fundamental_analyst(
            current_time: Annotated[
                Optional[str],
                Field(
                    description="Current timestamp to embed in the prompt. Defaults to server time."
                ),
            ] = None,
            tickers: Annotated[
                Optional[str],
                Field(
                    description="Comma-separated tickers under analysis (e.g. 'AAPL,MSFT')."
                ),
            ] = None,
        ) -> str:
            return self._resolve_prompt(
                "fundamental_analyst", current_time=current_time, tickers=tickers
            )

        @mcp.prompt(
            name="financial_analyst_v1_technical_analyst",
            description="System prompt for the Financial Analyst technical analyst step. "
            "Performs multi-indicator confluence analysis: trend (ADX/EMA), momentum "
            "(RSI/MACD), price positioning (52-week range). Produces a BUY/HOLD/SELL "
            "recommendation with a conviction score (1-10) per ticker.",
        )
        def financial_analyst_v1_technical_analyst(
            current_time: Annotated[
                Optional[str],
                Field(
                    description="Current timestamp to embed in the prompt. Defaults to server time."
                ),
            ] = None,
            tickers: Annotated[
                Optional[str],
                Field(
                    description="Comma-separated tickers under analysis (e.g. 'AAPL,MSFT')."
                ),
            ] = None,
        ) -> str:
            return self._resolve_prompt(
                "technical_analyst", current_time=current_time, tickers=tickers
            )

        @mcp.prompt(
            name="financial_analyst_v1_consensus_reporter",
            description="System prompt for the Financial Analyst consensus reporter step. "
            "Merges fundamental and technical recommendations into one voice, "
            "allocates USD 10,000 across tickers weighted by conviction, and "
            "produces a polished HTML report with per-ticker verdicts, allocation "
            "table, and a machine-parseable ALLOCATION: line.",
        )
        def financial_analyst_v1_consensus_reporter(
            current_time: Annotated[
                Optional[str],
                Field(
                    description="Current timestamp to embed in the prompt. Defaults to server time."
                ),
            ] = None,
            tickers: Annotated[
                Optional[str],
                Field(
                    description="Comma-separated tickers under analysis (e.g. 'AAPL,MSFT')."
                ),
            ] = None,
        ) -> str:
            return self._resolve_prompt(
                "consensus_reporter", current_time=current_time, tickers=tickers
            )

    def register_resources(self, mcp: FastMCP) -> None:
        @mcp.resource(
            uri="prompt://financial_analyst_v1_coordinator",
            name="financial_analyst_v1_coordinator",
            description="System prompt for the Financial Analyst coordinator step.",
        )
        def resource_coordinator() -> str:
            return self._resolve_prompt("coordinator")

        @mcp.resource(
            uri="prompt://financial_analyst_v1_data_collector",
            name="financial_analyst_v1_data_collector",
            description="System prompt for the Financial Analyst data collector step.",
        )
        def resource_data_collector() -> str:
            return self._resolve_prompt("data_collector")

        @mcp.resource(
            uri="prompt://financial_analyst_v1_fundamental_analyst",
            name="financial_analyst_v1_fundamental_analyst",
            description="System prompt for the Financial Analyst fundamental analyst step.",
        )
        def resource_fundamental_analyst() -> str:
            return self._resolve_prompt("fundamental_analyst")

        @mcp.resource(
            uri="prompt://financial_analyst_v1_technical_analyst",
            name="financial_analyst_v1_technical_analyst",
            description="System prompt for the Financial Analyst technical analyst step.",
        )
        def resource_technical_analyst() -> str:
            return self._resolve_prompt("technical_analyst")

        @mcp.resource(
            uri="prompt://financial_analyst_v1_consensus_reporter",
            name="financial_analyst_v1_consensus_reporter",
            description="System prompt for the Financial Analyst consensus reporter step.",
        )
        def resource_consensus_reporter() -> str:
            return self._resolve_prompt("consensus_reporter")
