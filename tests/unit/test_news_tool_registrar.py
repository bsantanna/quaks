from unittest.mock import MagicMock

import pytest

from app.interface.mcp.news_tool_registrar import NewsToolRegistrar, _render_prompt


class TestRenderPrompt:
    def test_renders_with_current_time(self):
        result = _render_prompt("Hello {{ CURRENT_TIME }}", current_time="Mon Jan 01 2025 12:00:00")
        assert "Mon Jan 01 2025 12:00:00" in result

    def test_renders_with_execution_plan(self):
        result = _render_prompt("Plan: {{ EXECUTION_PLAN }}", current_time="Mon Jan 01 2025 12:00:00")
        assert "coordinator" in result

    def test_renders_with_default_time(self):
        result = _render_prompt("Time: {{ CURRENT_TIME }}")
        assert result  # Should not be empty

    def test_empty_current_time_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            _render_prompt("Test", current_time="")

    def test_whitespace_current_time_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            _render_prompt("Test", current_time="   ")


class TestNewsToolRegistrar:
    def test_registers_tools(self):
        registrar = NewsToolRegistrar()
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_tools(mcp, container)
        tool_names = sorted(call[1]["name"] for call in mcp.tool.call_args_list)
        assert "get_markets_news_mcp" in tool_names
        assert "get_insights_news_mcp" in tool_names

    def test_registers_prompts(self):
        registrar = NewsToolRegistrar()
        mcp = MagicMock()
        registrar.register_prompts(mcp)
        prompt_names = [call[1]["name"] for call in mcp.prompt.call_args_list]
        assert "news_analyst_coordinator" in prompt_names
        assert "news_analyst_aggregator" in prompt_names
        assert "news_analyst_reporter" in prompt_names

    def test_registers_resources(self):
        registrar = NewsToolRegistrar()
        mcp = MagicMock()
        registrar.register_resources(mcp)
        resource_names = [call[1]["name"] for call in mcp.resource.call_args_list]
        assert "news_analyst_coordinator" in resource_names
        assert "news_analyst_aggregator" in resource_names
        assert "news_analyst_reporter" in resource_names
