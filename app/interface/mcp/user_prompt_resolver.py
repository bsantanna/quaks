from __future__ import annotations

import logging
from typing import Callable

from app.interface.mcp.schema import _get_mcp_schema
from app.services.agent_settings import AgentSettingService
from app.services.agents import AgentService

logger = logging.getLogger(__name__)


class UserPromptResolver:
    """Resolves an MCP-served prompt template, optionally overridden by the
    authenticated user's agent settings.

    When an authenticated user has an active agent of the given ``agent_type``
    in their tenant schema and that agent has a non-empty ``setting_key``
    value, the user's template is used. Otherwise ``default_template`` is
    used. Jinja render errors on the user template are logged and fall back
    to the default so skills keep working even when a user has saved a
    broken template.
    """

    def __init__(
        self,
        agent_service: AgentService,
        agent_setting_service: AgentSettingService,
    ) -> None:
        self._agent_service = agent_service
        self._agent_setting_service = agent_setting_service

    def resolve(
        self,
        agent_type: str,
        setting_key: str,
        default_template: str,
        render: Callable[[str], str],
    ) -> str:
        schema = _get_mcp_schema()
        user_template = self._lookup_user_template(schema, agent_type, setting_key)
        if user_template is not None:
            try:
                return render(user_template)
            except Exception as exc:
                logger.warning(
                    "User prompt template failed to render "
                    "(agent_type=%s, setting_key=%s, schema=%s): %s. "
                    "Falling back to default.",
                    agent_type,
                    setting_key,
                    schema,
                    exc,
                )
        return render(default_template)

    def _lookup_user_template(
        self, schema: str, agent_type: str, setting_key: str
    ) -> str | None:
        if schema == "public":
            return None
        agent = next(
            (
                a
                for a in self._agent_service.get_agents(schema)
                if a.agent_type == agent_type
            ),
            None,
        )
        if agent is None:
            return None
        for setting in self._agent_setting_service.get_agent_settings(agent.id, schema):
            if setting.setting_key == setting_key:
                value = setting.setting_value
                return value if value and value.strip() else None
        return None
