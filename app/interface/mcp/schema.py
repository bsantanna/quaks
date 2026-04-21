from typing import Optional

from fastmcp.server.dependencies import get_access_token
from pydantic import BaseModel, Field

from app.infrastructure.auth.user import get_schema


class AgentItem(BaseModel):
    """An AI agent registered on the Quaks platform."""

    id: str = Field(description="Unique agent identifier")
    agent_name: str = Field(description="Human-readable agent name")
    agent_type: str = Field(
        description="Agent type key (e.g. web_agent, supervised_workflow)"
    )
    agent_summary: str = Field(
        description="Brief description of the agent's purpose and capabilities"
    )
    language_model_id: Optional[str] = Field(
        default=None,
        description="ID of the language model powering this agent. "
        "Null when no model has been assigned yet.",
    )
    is_active: bool = Field(description="Whether the agent is currently active")


class NewsItem(BaseModel):
    """A single market news article."""

    id: Optional[str] = Field(
        default=None,
        description="Document identifier, usable with the id parameter to fetch this article directly",
    )
    headline: str = Field(description="Article headline")
    summary: str = Field(description="Short summary of the article")
    content: Optional[str] = Field(
        default=None,
        description="Full article text content. Only included when fetching a single article by id "
        "or when include_content=true is passed, since content is large and bulk responses "
        "should stay lean.",
    )
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

    id: Optional[str] = Field(
        default=None,
        description="Document identifier, usable with the id parameter to fetch this briefing directly",
    )
    date: str = Field(description="Briefing date in yyyy-mm-dd format")
    executive_summary: str = Field(
        description="Concise executive summary of the briefing"
    )
    report_html: Optional[str] = Field(
        default=None,
        description="Full HTML report content. Only included when include_report_html=true.",
    )
    language_model_name: Optional[str] = Field(
        default=None,
        description="Name of the language model that produced this briefing "
        "(e.g. 'claude-opus-4-7'). Null for briefings published before model "
        "provenance was tracked.",
    )


class InsightsNewsList(BaseModel):
    """Paginated list of AI-generated investor briefings."""

    items: list[InsightsNewsItem] = Field(
        description="Investor briefings matching the query"
    )
    cursor: Optional[str] = Field(
        default=None,
        description="Base64-encoded pagination cursor. Pass this value as the cursor "
        "parameter in the next request to fetch the next page. "
        "Null when there are no more results.",
    )


class PublishContentResult(BaseModel):
    """Result of a content publish operation."""

    status: str = Field(description="Publication status: 'published' on success")
    message: str = Field(description="Human-readable result message")
    doc_id: Optional[str] = Field(
        default=None,
        description="Document ID of the published content, for constructing the preview URL",
    )


def _get_mcp_schema() -> str:
    """Derive the tenant DB schema from the MCP access token."""
    access_token = get_access_token()
    if access_token is None:
        return "public"
    sub = access_token.claims.get("sub")
    user_id = f"id_{sub}" if sub else None
    return get_schema(user_id)
