from unittest.mock import MagicMock

import pytest

from app.interface.mcp.financial_analyst_v1_tool_registrar import (
    FinancialAnalystV1ToolRegistrar,
    _render_prompt,
)


def _passthrough_resolver():
    """Resolver mock that always renders the default template (no override)."""
    resolver = MagicMock()
    resolver.resolve.side_effect = (
        lambda agent_type, setting_key, default_template, render: render(
            default_template
        )
    )
    return resolver


def _capturing_mcp():
    """Return (mcp_mock, tools, prompts, resources) where each dict captures fn by name."""
    tools: dict = {}
    prompts: dict = {}
    resources: dict = {}

    def tool(**kwargs):
        def inner(fn):
            tools[kwargs["name"]] = fn
            return fn

        return inner

    def prompt(**kwargs):
        def inner(fn):
            prompts[kwargs["name"]] = fn
            return fn

        return inner

    def resource(**kwargs):
        def inner(fn):
            resources[kwargs["name"]] = fn
            return fn

        return inner

    mcp = MagicMock()
    mcp.tool.side_effect = tool
    mcp.prompt.side_effect = prompt
    mcp.resource.side_effect = resource
    return mcp, tools, prompts, resources


class TestRenderPrompt:
    def test_renders_with_current_time(self):
        result = _render_prompt(
            "Hello {{ CURRENT_TIME }}", current_time="Mon Jan 01 2025 12:00:00"
        )
        assert "Mon Jan 01 2025 12:00:00" in result

    def test_renders_with_execution_plan(self):
        result = _render_prompt(
            "Plan: {{ EXECUTION_PLAN }}", current_time="Mon Jan 01 2025 12:00:00"
        )
        assert "data_collector" in result
        assert "fundamental_analyst" in result

    def test_renders_with_tickers(self):
        result = _render_prompt(
            "Tickers: {{ TICKERS }}",
            current_time="Mon Jan 01 2025 12:00:00",
            tickers="AAPL,MSFT",
        )
        assert "AAPL,MSFT" in result

    def test_renders_default_tickers_placeholder(self):
        result = _render_prompt(
            "Tickers: {{ TICKERS }}", current_time="Mon Jan 01 2025 12:00:00"
        )
        assert "To be determined" in result

    def test_renders_with_default_time(self):
        result = _render_prompt("Time: {{ CURRENT_TIME }}")
        assert result  # should not be empty

    def test_empty_current_time_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            _render_prompt("Test", current_time="")

    def test_whitespace_current_time_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            _render_prompt("Test", current_time="   ")

    def test_empty_tickers_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            _render_prompt("Test", tickers="")

    def test_sandbox_blocks_attribute_access_ssti(self):
        from jinja2.exceptions import SecurityError

        payload = "{{ ''.__class__.__mro__[1].__subclasses__() }}"
        with pytest.raises(SecurityError):
            _render_prompt(payload, current_time="Mon Jan 01 2025 12:00:00")


class TestFinancialAnalystV1ToolRegistrar:
    def test_registers_tools(self):
        registrar = FinancialAnalystV1ToolRegistrar(_passthrough_resolver())
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_tools(mcp, container)
        tool_names = sorted(call[1]["name"] for call in mcp.tool.call_args_list)
        assert "fetch_company_profile_mcp" in tool_names
        assert "fetch_stats_close_mcp" in tool_names
        assert "fetch_technical_indicators_mcp" in tool_names
        assert "fetch_portfolio_xray_mcp" in tool_names

    def test_registers_prompts(self):
        registrar = FinancialAnalystV1ToolRegistrar(_passthrough_resolver())
        mcp = MagicMock()
        registrar.register_prompts(mcp)
        prompt_names = [call[1]["name"] for call in mcp.prompt.call_args_list]
        for role in (
            "coordinator",
            "data_collector",
            "fundamental_analyst",
            "technical_analyst",
            "consensus_reporter",
        ):
            assert f"financial_analyst_v1_{role}" in prompt_names

    def test_registers_resources(self):
        registrar = FinancialAnalystV1ToolRegistrar(_passthrough_resolver())
        mcp = MagicMock()
        registrar.register_resources(mcp)
        resource_names = [call[1]["name"] for call in mcp.resource.call_args_list]
        for role in (
            "coordinator",
            "data_collector",
            "fundamental_analyst",
            "technical_analyst",
            "consensus_reporter",
        ):
            assert f"financial_analyst_v1_{role}" in resource_names


class TestFetchCompanyProfileMcp:
    @pytest.mark.asyncio
    async def test_calls_service_with_uppercased_ticker(self):
        container = MagicMock()
        container.markets_stats_service.return_value.get_company_profile.return_value = {
            "name": "Apple",
            "sector": "Technology",
        }
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(_passthrough_resolver()).register_tools(
            mcp, container
        )

        result = await tools["fetch_company_profile_mcp"](ticker="aapl")

        assert result == {"name": "Apple", "sector": "Technology"}
        call_kwargs = (
            container.markets_stats_service.return_value.get_company_profile.call_args[
                1
            ]
        )
        assert call_kwargs["key_ticker"] == "AAPL"
        assert call_kwargs["index_name"] == "quaks_stocks-metadata_latest"


class TestFetchStatsCloseMcp:
    @pytest.mark.asyncio
    async def test_defaults_date_range(self):
        container = MagicMock()
        container.markets_stats_service.return_value.get_stats_close.return_value = {
            "latest_close": 100
        }
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(_passthrough_resolver()).register_tools(
            mcp, container
        )

        result = await tools["fetch_stats_close_mcp"](ticker="AAPL")

        assert result == {"latest_close": 100}
        call_kwargs = (
            container.markets_stats_service.return_value.get_stats_close.call_args[1]
        )
        assert call_kwargs["start_date"] is not None
        assert call_kwargs["end_date"] is not None
        assert call_kwargs["key_ticker"] == "AAPL"

    @pytest.mark.asyncio
    async def test_explicit_date_range(self):
        container = MagicMock()
        container.markets_stats_service.return_value.get_stats_close.return_value = {}
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(_passthrough_resolver()).register_tools(
            mcp, container
        )

        await tools["fetch_stats_close_mcp"](
            ticker="MSFT", start_date="2026-01-01", end_date="2026-04-01"
        )

        call_kwargs = (
            container.markets_stats_service.return_value.get_stats_close.call_args[1]
        )
        assert call_kwargs["start_date"] == "2026-01-01"
        assert call_kwargs["end_date"] == "2026-04-01"


class TestFetchTechnicalIndicatorsMcp:
    @pytest.mark.asyncio
    async def test_calls_all_four_indicators(self):
        container = MagicMock()
        svc = container.markets_stats_service.return_value
        svc.get_indicator_rsi.return_value = {"rsi": 50}
        svc.get_indicator_macd.return_value = {"macd": 1}
        svc.get_indicator_ema.return_value = {"ema": 2}
        svc.get_indicator_adx.return_value = {"adx": 3}
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(_passthrough_resolver()).register_tools(
            mcp, container
        )

        result = await tools["fetch_technical_indicators_mcp"](ticker="nvda")

        assert set(result.keys()) == {"rsi", "macd", "ema", "adx"}
        assert svc.get_indicator_rsi.call_args[1]["key_ticker"] == "NVDA"
        assert svc.get_indicator_rsi.call_args[1]["period"] == 14
        assert svc.get_indicator_macd.call_args[1]["short_window"] == 12
        assert svc.get_indicator_macd.call_args[1]["long_window"] == 26
        assert svc.get_indicator_macd.call_args[1]["signal_window"] == 9
        assert svc.get_indicator_ema.call_args[1]["short_window"] == 10
        assert svc.get_indicator_ema.call_args[1]["long_window"] == 20
        assert svc.get_indicator_adx.call_args[1]["period"] == 14


class TestFetchPortfolioXrayMcp:
    @pytest.mark.asyncio
    async def test_returns_text_summary(self):
        container = MagicMock()
        container.markets_stats_service.return_value.get_company_profile.return_value = {
            "name": "Apple",
            "sector": "Technology",
            "country": "US",
            "market_capitalization": 3_000_000_000_000,
            "pe_ratio": 30,
        }
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(_passthrough_resolver()).register_tools(
            mcp, container
        )

        result = await tools["fetch_portfolio_xray_mcp"](tickers="aapl,msft")

        assert isinstance(result, str)
        assert "PORTFOLIO X-RAY" in result

    @pytest.mark.asyncio
    async def test_empty_profiles_returns_fallback(self):
        container = MagicMock()
        container.markets_stats_service.return_value.get_company_profile.return_value = {}
        mcp, tools, _, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(_passthrough_resolver()).register_tools(
            mcp, container
        )

        result = await tools["fetch_portfolio_xray_mcp"](tickers="XXXX")

        assert result == "No metadata available."


class TestPromptsAndResources:
    _ROLES = (
        "coordinator",
        "data_collector",
        "fundamental_analyst",
        "technical_analyst",
        "consensus_reporter",
    )

    def test_prompt_functions_return_rendered_strings(self):
        mcp, _, prompts, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(_passthrough_resolver()).register_prompts(mcp)

        for role in self._ROLES:
            result = prompts[f"financial_analyst_v1_{role}"]()
            assert isinstance(result, str)
            assert result

    def test_prompt_functions_accept_current_time_and_tickers(self):
        mcp, _, prompts, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(_passthrough_resolver()).register_prompts(mcp)

        result = prompts["financial_analyst_v1_data_collector"](
            current_time="Mon Jan 01 2025 12:00:00",
            tickers="AAPL,MSFT",
        )
        assert "Mon Jan 01 2025 12:00:00" in result
        assert "AAPL,MSFT" in result

    def test_resource_functions_return_rendered_strings(self):
        mcp, _, _, resources = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(_passthrough_resolver()).register_resources(mcp)

        for role in self._ROLES:
            result = resources[f"financial_analyst_v1_{role}"]()
            assert isinstance(result, str)
            assert result


class TestUserOverrideWiring:
    """Verify each prompt/resource delegates to the resolver with the right keys."""

    _EXPECTED = [
        ("coordinator", "coordinator_system_prompt"),
        ("data_collector", "data_collector_system_prompt"),
        ("fundamental_analyst", "fundamental_analyst_system_prompt"),
        ("technical_analyst", "technical_analyst_system_prompt"),
        ("consensus_reporter", "consensus_reporter_system_prompt"),
    ]

    def test_prompts_call_resolver_with_role_specific_keys(self):
        resolver = MagicMock()
        resolver.resolve.return_value = "RESOLVED"
        mcp, _, prompts, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(resolver).register_prompts(mcp)

        for role, setting_key in self._EXPECTED:
            resolver.resolve.reset_mock()
            result = prompts[f"financial_analyst_v1_{role}"]()
            assert result == "RESOLVED"
            kwargs = resolver.resolve.call_args.kwargs
            assert kwargs["agent_type"] == "quaks_financial_analyst_v1"
            assert kwargs["setting_key"] == setting_key
            assert kwargs["default_template"]  # non-empty

    def test_resources_call_resolver_with_role_specific_keys(self):
        resolver = MagicMock()
        resolver.resolve.return_value = "RESOLVED"
        mcp, _, _, resources = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(resolver).register_resources(mcp)

        for role, setting_key in self._EXPECTED:
            resolver.resolve.reset_mock()
            result = resources[f"financial_analyst_v1_{role}"]()
            assert result == "RESOLVED"
            kwargs = resolver.resolve.call_args.kwargs
            assert kwargs["agent_type"] == "quaks_financial_analyst_v1"
            assert kwargs["setting_key"] == setting_key

    def test_prompt_render_closure_includes_current_time_and_tickers(self):
        resolver = MagicMock()
        captured = {}

        def capture(agent_type, setting_key, default_template, render):
            captured["rendered"] = render(
                "Time: {{ CURRENT_TIME }} | Tickers: {{ TICKERS }}"
            )
            return captured["rendered"]

        resolver.resolve.side_effect = capture
        mcp, _, prompts, _ = _capturing_mcp()
        FinancialAnalystV1ToolRegistrar(resolver).register_prompts(mcp)

        prompts["financial_analyst_v1_fundamental_analyst"](
            current_time="Mon Jan 01 2025 12:00:00",
            tickers="AAPL,MSFT,NVDA",
        )
        assert "Mon Jan 01 2025 12:00:00" in captured["rendered"]
        assert "AAPL,MSFT,NVDA" in captured["rendered"]
