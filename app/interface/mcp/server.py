import os
from datetime import datetime, timedelta
from html import unescape
from typing import Annotated, Optional

from fastmcp import FastMCP
from jinja2 import Template
from pydantic import BaseModel, Field

from app.core.container import Container
from app.services.agent_types.quaks.insights.news.prompts import (
    AGGREGATOR_SYSTEM_PROMPT,
    COORDINATOR_SYSTEM_PROMPT,
    REPORTER_SYSTEM_PROMPT,
)

_EXECUTION_PLAN = (
    "News analysis plan:\n"
    "1. coordinator: Decide whether to proceed with news analysis\n"
    "2. aggregator: Fetch latest news from the last 24 hours and prioritize by economic impact\n"
    "3. reporter: Group articles by topic, write 4-paragraph summaries, and produce the final briefing"
)


# -- Response models --


class AgentItem(BaseModel):
    """An AI agent registered on the Quaks platform."""

    id: str = Field(description="Unique agent identifier")
    agent_name: str = Field(description="Human-readable agent name")
    agent_type: str = Field(description="Agent type key (e.g. web_agent, supervised_workflow)")
    agent_summary: str = Field(description="Brief description of the agent's purpose and capabilities")
    language_model_id: str = Field(description="ID of the language model powering this agent")
    is_active: bool = Field(description="Whether the agent is currently active")


class NewsItem(BaseModel):
    """A single market news article."""

    headline: str = Field(description="Article headline")
    summary: str = Field(description="Short summary of the article")
    content: str = Field(description="Full article text content")
    source: str = Field(description="News source name (e.g. Reuters, Bloomberg)")
    date: str = Field(description="Publication date in yyyy-mm-dd format")
    tickers: Optional[list[str]] = Field(
        default=None, description="Stock ticker symbols mentioned in the article"
    )


class NewsList(BaseModel):
    """Paginated list of market news articles."""

    items: list[NewsItem] = Field(description="News articles matching the query")
    cursor: Optional[str] = Field(
        default=None,
        description="Base64-encoded pagination cursor. Pass this value as the cursor "
        "parameter in the next request to fetch the next page of results. "
        "Null when there are no more results.",
    )


class InsightsNewsItem(BaseModel):
    """An AI-generated investor briefing produced by Quaks analyst agents."""

    date: str = Field(description="Briefing date in yyyy-mm-dd format")
    executive_summary: str = Field(
        description="Concise executive summary of the briefing"
    )
    report_html: Optional[str] = Field(
        default=None,
        description="Full HTML report content. Only included when include_report_html=true.",
    )


class InsightsNewsList(BaseModel):
    """Paginated list of AI-generated investor briefings."""

    items: list[InsightsNewsItem] = Field(description="Investor briefings matching the query")
    cursor: Optional[str] = Field(
        default=None,
        description="Base64-encoded pagination cursor. Pass this value as the cursor "
        "parameter in the next request to fetch the next page. "
        "Null when there are no more results.",
    )


# -- Server setup --

_SERVER_INSTRUCTIONS = """Quaks is a multi-agent financial intelligence platform.

Available tools:
- get_agent_list: Discover AI agents available on the platform.
- get_markets_news_mcp: Search and retrieve market news articles filtered by ticker, topic, or date range.
- get_insights_news_mcp: Retrieve AI-generated investor briefings with executive summaries.

Available prompts (news_analyst workflow):
- news_analyst_coordinator: System prompt for the coordinator step — answers user questions directly (QA mode) or routes to the aggregator for briefing generation.
- news_analyst_aggregator: System prompt for the aggregator step — collects and prioritizes market news by economic impact. Use with get_markets_news_mcp tool.
- news_analyst_reporter: System prompt for the reporter step — groups articles, writes summaries, and produces the final HTML briefing.

To replicate the full News Analyst workflow:
1. Use news_analyst_coordinator prompt with user's question. If the user wants a briefing, proceed to step 2.
2. Use news_analyst_aggregator prompt + get_markets_news_mcp tool to collect and prioritize news.
3. Use news_analyst_reporter prompt with the aggregated news to produce the final HTML briefing.

Pagination: The news tools return a `cursor` field. To get the next page, pass the cursor value back in the next call. When cursor is null, there are no more results.

Date format: All dates use yyyy-mm-dd format (e.g. 2025-01-15).
"""


def build_mcp_server(container: Container) -> FastMCP:
    config = container.config()
    auth = _build_auth(config)

    mcp = FastMCP(
        name=os.getenv("SERVICE_NAME", "Quaks"),
        version=os.getenv("SERVICE_VERSION", "snapshot"),
        instructions=_SERVER_INSTRUCTIONS,
        auth=auth,
    )

    _register_tools(mcp, container)
    _register_prompts(mcp)
    _register_resources(mcp)
    return mcp


def _build_auth(config: dict):
    if not config["auth"]["enabled"]:
        return None

    from fastmcp.server.auth import OAuthProxy
    from fastmcp.server.auth.providers.jwt import JWTVerifier

    auth_url = config["auth"]["url"]
    realm = config["auth"]["realm"]
    realm_base = f"{auth_url}/realms/{realm}"

    return OAuthProxy(
        upstream_authorization_endpoint=f"{realm_base}/protocol/openid-connect/auth",
        upstream_token_endpoint=f"{realm_base}/protocol/openid-connect/token",
        upstream_client_id=config["auth"]["client_id"],
        upstream_client_secret=config["auth"]["client_secret"],
        token_verifier=JWTVerifier(
            jwks_uri=f"{realm_base}/protocol/openid-connect/certs",
            issuer=realm_base,
            audience="account",
            required_scopes=["openid", "profile", "email"],
        ),
        base_url=f"{config['api_base_url']}/mcp",
    )


def _register_tools(mcp: FastMCP, container: Container) -> None:

    @mcp.tool(
        name="get_agent_list",
        description="List all AI agents registered on the Quaks platform. "
        "Returns each agent's ID, name, type, capabilities summary, "
        "and linked language model. Use this to discover what agents "
        "are available and what they can do.",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    async def get_agent_list() -> list[AgentItem]:
        agent_service = container.agent_service()
        agents = agent_service.get_agents("public")
        return [
            AgentItem(
                id=a.id,
                agent_name=a.agent_name,
                agent_type=a.agent_type,
                agent_summary=a.agent_summary,
                language_model_id=a.language_model_id,
                is_active=a.is_active,
            )
            for a in agents
        ]

    @mcp.tool(
        name="get_markets_news_mcp",
        description="Search and retrieve recent market news articles. "
        "Articles include headline, summary, full content, source, "
        "date, and related ticker symbols. Results are optimized for "
        "LLM consumption. Supports filtering by ticker symbol, "
        "free-text search, and date range. Returns up to 15 articles "
        "per page with cursor-based pagination.",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    async def get_markets_news_mcp(
        search_term: Annotated[
            Optional[str],
            Field(description="Free-text search filter (e.g. 'artificial intelligence', 'earnings')"),
        ] = None,
        key_ticker: Annotated[
            Optional[str],
            Field(description="Stock ticker symbol to filter by (e.g. 'AAPL', 'MSFT', 'NVDA')"),
        ] = None,
        date_from: Annotated[
            Optional[str],
            Field(description="Start date filter in yyyy-mm-dd format. Defaults to yesterday."),
        ] = None,
        date_to: Annotated[
            Optional[str],
            Field(description="End date filter in yyyy-mm-dd format. Defaults to today."),
        ] = None,
        cursor: Annotated[
            Optional[str],
            Field(description="Pagination cursor from a previous response to fetch the next page"),
        ] = None,
        size: Annotated[
            int,
            Field(description="Number of articles to return (1-15)", ge=1, le=15),
        ] = 3,
    ) -> NewsList:
        svc = container.markets_news_service()
        resolved_from = date_from or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        results, sort = await svc.get_news(
            index_name="quaks_markets-news_latest",
            search_term=search_term,
            key_ticker=key_ticker,
            date_from=resolved_from,
            date_to=date_to,
            size=min(max(size, 1), 15),
            cursor=cursor,
            include_text_content=True,
            include_key_ticker=True,
        )

        items = [
            NewsItem(
                headline=unescape(h["_source"].get("text_headline") or ""),
                summary=unescape(h["_source"].get("text_summary") or ""),
                content=unescape(h["_source"].get("text_content") or ""),
                source=h["_source"].get("key_source", ""),
                date=h["_source"].get("date_reference", ""),
                tickers=h["_source"].get("key_ticker"),
            )
            for h in results
        ]
        return NewsList(items=items, cursor=sort)

    @mcp.tool(
        name="get_insights_news_mcp",
        description="Retrieve AI-generated investor briefings produced by "
        "Quaks analyst agents. Each briefing contains an executive summary "
        "and optionally the full HTML report. Use this to get synthesized "
        "market intelligence and analysis. Returns up to 15 briefings "
        "per page with cursor-based pagination.",
        annotations={"readOnlyHint": True, "openWorldHint": False},
    )
    async def get_insights_news_mcp(
        date_from: Annotated[
            Optional[str],
            Field(description="Start date filter in yyyy-mm-dd format"),
        ] = None,
        date_to: Annotated[
            Optional[str],
            Field(description="End date filter in yyyy-mm-dd format"),
        ] = None,
        cursor: Annotated[
            Optional[str],
            Field(description="Pagination cursor from a previous response to fetch the next page"),
        ] = None,
        size: Annotated[
            int,
            Field(description="Number of briefings to return (1-15)", ge=1, le=15),
        ] = 3,
        include_report_html: Annotated[
            bool,
            Field(description="Set to true to include the full HTML report in each briefing. "
                  "Increases response size significantly."),
        ] = False,
    ) -> InsightsNewsList:
        svc = container.markets_insights_service()

        results, sort = await svc.get_insights_news(
            index_name="quaks_insights-news_latest",
            date_from=date_from,
            date_to=date_to,
            size=min(max(size, 1), 15),
            cursor=cursor,
            include_report_html=include_report_html,
        )

        items = [
            InsightsNewsItem(
                date=h["_source"].get("date_reference", ""),
                executive_summary=unescape(h["_source"].get("text_executive_summary") or ""),
                report_html=unescape(h["_source"].get("text_report_html") or "")
                if include_report_html
                else None,
            )
            for h in results
        ]
        return InsightsNewsList(items=items, cursor=sort)


def _register_resources(mcp: FastMCP) -> None:

    @mcp.resource(
        uri="prompt://news_analyst_coordinator",
        name="news_analyst_coordinator",
        description="System prompt for the News Analyst coordinator step.",
    )
    def resource_coordinator() -> str:
        return _render_prompt(COORDINATOR_SYSTEM_PROMPT)

    @mcp.resource(
        uri="prompt://news_analyst_aggregator",
        name="news_analyst_aggregator",
        description="System prompt for the News Analyst aggregator step.",
    )
    def resource_aggregator() -> str:
        return _render_prompt(AGGREGATOR_SYSTEM_PROMPT)

    @mcp.resource(
        uri="prompt://news_analyst_reporter",
        name="news_analyst_reporter",
        description="System prompt for the News Analyst reporter step.",
    )
    def resource_reporter() -> str:
        return _render_prompt(REPORTER_SYSTEM_PROMPT)


def _render_prompt(template_str: str) -> str:
    template = Template(template_str)
    return template.render(
        CURRENT_TIME=datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
        EXECUTION_PLAN=_EXECUTION_PLAN,
    )


def _register_prompts(mcp: FastMCP) -> None:

    @mcp.prompt(
        name="news_analyst_coordinator",
        description="System prompt for the News Analyst coordinator step. "
        "In QA mode, this prompt instructs the LLM to answer financial "
        "questions using investor briefings from get_insights_news_mcp. "
        "In briefing mode (input 'BATCH_ETL'), it routes to the aggregator. "
        "Returns a ready-to-use system prompt with current timestamp.",
    )
    def news_analyst_coordinator() -> str:
        return _render_prompt(COORDINATOR_SYSTEM_PROMPT)

    @mcp.prompt(
        name="news_analyst_aggregator",
        description="System prompt for the News Analyst aggregator step. "
        "Instructs the LLM to collect market news via get_markets_news_mcp, "
        "sort articles by economic impact, and write a market mood summary. "
        "Returns a ready-to-use system prompt with current timestamp and execution plan.",
    )
    def news_analyst_aggregator() -> str:
        return _render_prompt(AGGREGATOR_SYSTEM_PROMPT)

    @mcp.prompt(
        name="news_analyst_reporter",
        description="System prompt for the News Analyst reporter step. "
        "Instructs the LLM to group aggregated articles by topic, write "
        "4-paragraph summaries (what happened, why it matters, bigger picture, "
        "what to watch), and produce the final investor briefing in HTML format. "
        "Returns a ready-to-use system prompt with current timestamp and execution plan.",
    )
    def news_analyst_reporter() -> str:
        return _render_prompt(REPORTER_SYSTEM_PROMPT)
