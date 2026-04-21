from unittest.mock import MagicMock, patch

import pytest

from app.domain.exceptions.base import DuplicateEntryError, UnauthorizedSkillError
from app.interface.mcp.default_tool_registrar import DefaultToolRegistrar


def _capturing_mcp():
    """Return (mcp_mock, captured) where captured[name] holds each registered tool fn."""
    captured: dict = {}

    def tool(**kwargs):
        def inner(fn):
            captured[kwargs["name"]] = fn
            return fn

        return inner

    mcp = MagicMock()
    mcp.tool.side_effect = tool
    return mcp, captured


class TestDefaultToolRegistrar:
    def test_registers_tools(self):
        registrar = DefaultToolRegistrar()
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_tools(mcp, container)
        tool_names = sorted(call[1]["name"] for call in mcp.tool.call_args_list)
        assert "get_agent_list" in tool_names
        assert "publish_content_mcp" in tool_names


class TestGetAgentList:
    @pytest.mark.asyncio
    @patch("app.interface.mcp.default_tool_registrar._get_mcp_schema")
    async def test_returns_mapped_agents(self, mock_schema):
        mock_schema.return_value = "id_abc"
        agent = MagicMock(
            id="a1",
            agent_name="Analyst",
            agent_type="supervised_workflow",
            agent_summary="summary",
            language_model_id="lm1",
            is_active=True,
        )
        container = MagicMock()
        container.agent_service.return_value.get_agents.return_value = [agent]

        mcp, captured = _capturing_mcp()
        DefaultToolRegistrar().register_tools(mcp, container)

        result = await captured["get_agent_list"]()

        container.agent_service.return_value.get_agents.assert_called_once_with("id_abc")
        assert len(result) == 1
        assert result[0].id == "a1"
        assert result[0].language_model_id == "lm1"

    @pytest.mark.asyncio
    @patch("app.interface.mcp.default_tool_registrar._get_mcp_schema")
    async def test_handles_null_language_model(self, mock_schema):
        mock_schema.return_value = "public"
        agent = MagicMock(
            id="a1",
            agent_name="Agent",
            agent_type="test_echo",
            agent_summary="s",
            language_model_id=None,
            is_active=False,
        )
        container = MagicMock()
        container.agent_service.return_value.get_agents.return_value = [agent]

        mcp, captured = _capturing_mcp()
        DefaultToolRegistrar().register_tools(mcp, container)

        result = await captured["get_agent_list"]()
        assert result[0].language_model_id is None


class TestPublishContentMcp:
    @pytest.mark.asyncio
    @patch("app.interface.mcp.default_tool_registrar.get_access_token")
    async def test_publish_success(self, mock_token):
        mock_token.return_value = MagicMock(claims={"preferred_username": "alice"})
        container = MagicMock()
        container.published_content_service.return_value.publish.return_value = "doc-1"

        mcp, captured = _capturing_mcp()
        DefaultToolRegistrar().register_tools(mcp, container)

        result = await captured["publish_content_mcp"](
            text_executive_summary="summary",
            text_report_html="<p>report</p>",
            key_skill_name="/news_analyst",
            language_model_name="claude-opus-4-7",
        )

        assert result.status == "published"
        assert result.doc_id == "doc-1"
        assert "alice" in result.message
        container.published_content_service.return_value.publish.assert_called_once_with(
            executive_summary="summary",
            report_html="<p>report</p>",
            skill_name="/news_analyst",
            author_username="alice",
            language_model_name="claude-opus-4-7",
        )

    @pytest.mark.asyncio
    @patch("app.interface.mcp.default_tool_registrar.get_access_token")
    async def test_publish_duplicate(self, mock_token):
        mock_token.return_value = MagicMock(claims={"preferred_username": "alice"})
        container = MagicMock()
        container.published_content_service.return_value.publish.side_effect = (
            DuplicateEntryError("Content")
        )

        mcp, captured = _capturing_mcp()
        DefaultToolRegistrar().register_tools(mcp, container)

        result = await captured["publish_content_mcp"](
            text_executive_summary="s",
            text_report_html="<p>r</p>",
            key_skill_name="/news_analyst",
            language_model_name="claude-opus-4-7",
        )

        assert result.status == "duplicate"
        assert result.doc_id is None

    @pytest.mark.asyncio
    @patch("app.interface.mcp.default_tool_registrar.get_access_token")
    async def test_publish_rejected_unauthorized_skill(self, mock_token):
        mock_token.return_value = MagicMock(claims={"preferred_username": "alice"})
        container = MagicMock()
        container.published_content_service.return_value.publish.side_effect = (
            UnauthorizedSkillError("/quant_analyst")
        )

        mcp, captured = _capturing_mcp()
        DefaultToolRegistrar().register_tools(mcp, container)

        result = await captured["publish_content_mcp"](
            text_executive_summary="s",
            text_report_html="<p>r</p>",
            key_skill_name="/quant_analyst",
            language_model_name="claude-opus-4-7",
        )

        assert result.status == "rejected"
        assert "/quant_analyst" in result.message

    @pytest.mark.asyncio
    @patch("app.interface.mcp.default_tool_registrar.get_access_token", return_value=None)
    async def test_publish_requires_auth(self, mock_token):
        container = MagicMock()
        mcp, captured = _capturing_mcp()
        DefaultToolRegistrar().register_tools(mcp, container)

        with pytest.raises(ValueError, match="Authentication required"):
            await captured["publish_content_mcp"](
                text_executive_summary="s",
                text_report_html="<p>r</p>",
                key_skill_name="/news_analyst",
                language_model_name="claude-opus-4-7",
            )

    @pytest.mark.asyncio
    @patch("app.interface.mcp.default_tool_registrar.get_access_token")
    async def test_publish_requires_username_claim(self, mock_token):
        mock_token.return_value = MagicMock(claims={})
        container = MagicMock()
        mcp, captured = _capturing_mcp()
        DefaultToolRegistrar().register_tools(mcp, container)

        with pytest.raises(ValueError, match="Authentication required"):
            await captured["publish_content_mcp"](
                text_executive_summary="s",
                text_report_html="<p>r</p>",
                key_skill_name="/news_analyst",
                language_model_name="claude-opus-4-7",
            )
