from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from pydantic import Field

from app.domain.exceptions.base import DuplicateEntryError
from app.interface.mcp.registrar import McpRegistrar
from app.interface.mcp.schema import (
    AgentItem,
    PublishContentResult,
    _get_mcp_schema,
)

if TYPE_CHECKING:
    from app.core.container import Container


class DefaultToolRegistrar(McpRegistrar):
    """Registers the default Quaks MCP tools."""

    def register_tools(self, mcp: FastMCP, container: Container) -> None:
        @mcp.tool(
            name="get_agent_list",
            description="List all AI agents registered on the Quaks platform. "
            "Returns each agent's ID, name, type, capabilities summary, "
            "and linked language model. Use this to discover what agents "
            "are available and what they can do.",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def get_agent_list() -> list[AgentItem]:
            schema = _get_mcp_schema()
            agent_service = container.agent_service()
            agents = agent_service.get_agents(schema)
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
            name="publish_content_mcp",
            description="Publish AI-generated content (reports, briefings, analysis) "
            "to the Quaks platform. The content is queued for validation and "
            "then routed to the appropriate index based on the skill that "
            "produced it. Requires authentication — the author is identified "
            "from the access token. IMPORTANT: Convert any Markdown content "
            "to well-formed HTML before calling this tool.",
            annotations={"readOnlyHint": False, "openWorldHint": False},
        )
        async def publish_content_mcp(
            text_executive_summary: Annotated[
                str,
                Field(description="Concise executive summary of the content"),
            ],
            text_report_html: Annotated[
                str,
                Field(
                    description="Full report content in HTML format. "
                    "Convert Markdown to HTML before submitting."
                ),
            ],
            key_skill_name: Annotated[
                str,
                Field(
                    description="Name of the skill that generated this content "
                    "(e.g. '/news_analyst')"
                ),
            ],
        ) -> PublishContentResult:
            access_token = get_access_token()
            if access_token is None or not access_token.claims.get(
                "preferred_username"
            ):
                raise ValueError(
                    "Authentication required. No valid access token or username found."
                )
            author_username = access_token.claims["preferred_username"]

            try:
                svc = container.published_content_service()
                doc_id = svc.publish(
                    executive_summary=text_executive_summary,
                    report_html=text_report_html,
                    skill_name=key_skill_name,
                    author_username=author_username,
                )
            except DuplicateEntryError:
                return PublishContentResult(
                    status="duplicate",
                    message="Content with this summary from this author already exists.",
                )

            return PublishContentResult(
                status="published",
                doc_id=doc_id,
                message=f"Content published successfully by {author_username}. "
                "It will be validated and routed to the appropriate index.",
            )
