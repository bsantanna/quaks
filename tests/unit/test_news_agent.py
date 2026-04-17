"""Tests for QuaksNewsAnalystAgent."""
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.constants import END

from app.services.agent_types.base import AgentUtils
from app.services.agent_types.quaks.insights.news.agent import QuaksNewsAnalystAgent


def _make_agent_utils():
    return AgentUtils(
        agent_service=MagicMock(),
        agent_setting_service=MagicMock(),
        attachment_service=MagicMock(),
        language_model_service=MagicMock(),
        language_model_setting_service=MagicMock(),
        integration_service=MagicMock(),
        vault_client=MagicMock(),
        graph_persistence_factory=MagicMock(),
        document_repository=MagicMock(),
        task_notification_service=MagicMock(),
        config=MagicMock(),
    )


class TestCreateDefaultSettings:
    def test_creates_three_prompts(self):
        utils = _make_agent_utils()
        agent = QuaksNewsAnalystAgent(utils, MagicMock(), MagicMock())
        agent.create_default_settings("agent-1", "public")
        calls = utils.agent_setting_service.create_agent_setting.call_args_list
        keys = [c[1]["setting_key"] for c in calls]
        assert "coordinator_system_prompt" in keys
        assert "aggregator_system_prompt" in keys
        assert "reporter_system_prompt" in keys
        assert len(keys) == 3


class TestGetWorkflowBuilder:
    def test_returns_state_graph(self):
        utils = _make_agent_utils()
        agent = QuaksNewsAnalystAgent(utils, MagicMock(), MagicMock())
        builder = agent.get_workflow_builder("agent-1")
        assert builder is not None
        assert "coordinator" in builder.nodes
        assert "aggregator" in builder.nodes
        assert "reporter" in builder.nodes


class TestIsBriefingRequest:
    def test_briefing_keywords(self):
        utils = _make_agent_utils()
        agent = QuaksNewsAnalystAgent(utils, MagicMock(), MagicMock())
        assert agent._is_briefing_request("Give me a briefing") is True
        assert agent._is_briefing_request("news summary please") is True
        assert agent._is_briefing_request("daily digest") is True
        assert agent._is_briefing_request("market overview") is True
        assert agent._is_briefing_request("give me a recap") is True

    def test_non_briefing_queries(self):
        utils = _make_agent_utils()
        agent = QuaksNewsAnalystAgent(utils, MagicMock(), MagicMock())
        assert agent._is_briefing_request("What is AAPL stock price?") is False
        assert agent._is_briefing_request("hello") is False


class TestExtractExecutiveSummary:
    def test_extracts_blockquote(self):
        html = "<h1>Report</h1><blockquote>This is the summary.</blockquote><p>More</p>"
        result = QuaksNewsAnalystAgent._extract_executive_summary(html)
        assert result == "This is the summary."

    def test_no_blockquote(self):
        result = QuaksNewsAnalystAgent._extract_executive_summary("<p>No blockquote</p>")
        assert result == ""


class TestFormatResponse:
    def test_returns_report_html(self):
        utils = _make_agent_utils()
        agent = QuaksNewsAnalystAgent(utils, MagicMock(), MagicMock())
        state = {
            "messages": [
                HumanMessage(content="BATCH_ETL"),
                AIMessage(content="<h1>Report</h1>"),
            ],
            "executive_summary": "Summary text",
        }
        content, data = agent.format_response(state)
        assert content == "<h1>Report</h1>"
        assert data["executive_summary"] == "Summary text"
        assert data["report_html"] == "<h1>Report</h1>"


class TestStubMethods:
    def test_get_planner(self):
        utils = _make_agent_utils()
        agent = QuaksNewsAnalystAgent(utils, MagicMock(), MagicMock())
        result = agent.get_planner({})
        assert result.goto == "supervisor"

    def test_get_supervisor(self):
        utils = _make_agent_utils()
        agent = QuaksNewsAnalystAgent(utils, MagicMock(), MagicMock())
        result = agent.get_supervisor({})
        assert result.goto == END
