from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastmcp import FastMCP
from mcp.types import Icon

from app.interface.mcp.registrar import McpRegistrar

if TYPE_CHECKING:
    from app.core.container import Container


_SERVER_INSTRUCTIONS = """Quaks is a multi-agent financial intelligence platform.

Available tools:
- get_agent_list: Discover AI agents available on the platform.
- get_markets_news_mcp: Search and retrieve market news articles filtered by ticker, topic, or date range.
- get_insights_news_mcp: Retrieve AI-generated investor briefings with executive summaries.
- publish_content_mcp: Publish AI-generated content (reports, briefings) to the platform. Requires authentication. Content must be in HTML format.

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


def build_mcp_server(
    container: Container,
    registrars: list[McpRegistrar],
) -> FastMCP:
    config = container.config()
    auth = _build_auth(config)

    base_url = config.get("api_base_url", "")
    mcp = FastMCP(
        name=os.getenv("SERVICE_NAME", "Quaks"),
        version=os.getenv("SERVICE_VERSION", "snapshot"),
        instructions=_SERVER_INSTRUCTIONS,
        auth=auth,
        icons=[Icon(src=f"{base_url}/logo.svg", mimeType="image/svg+xml")],
    )

    for registrar in registrars:
        registrar.register_tools(mcp, container)
        registrar.register_prompts(mcp)
        registrar.register_resources(mcp)

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
