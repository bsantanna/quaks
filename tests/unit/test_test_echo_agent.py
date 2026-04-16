from unittest.mock import MagicMock

from app.services.agent_types.test_echo.test_echo_agent import TestEchoAgent
from app.services.agent_types.base import AgentUtils
from app.interface.api.messages.schema import MessageRequest


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


class TestTestEchoAgent:
    def test_create_default_settings(self):
        utils = _make_agent_utils()
        agent = TestEchoAgent(utils)
        agent.create_default_settings("agent-1", "public")
        utils.agent_setting_service.create_agent_setting.assert_called_once_with(
            agent_id="agent-1",
            setting_key="dummy_setting",
            setting_value="dummy_value",
            schema="public",
        )

    def test_get_input_params(self):
        utils = _make_agent_utils()
        agent = TestEchoAgent(utils)
        req = MessageRequest(
            agent_id="agent-1",
            message_content="hello",
        )
        params = agent.get_input_params(req, "public")
        assert params["agent_id"] == "agent-1"
        assert params["message_content"] == "hello"

    def test_process_message(self):
        utils = _make_agent_utils()
        agent = TestEchoAgent(utils)
        req = MessageRequest(
            agent_id="agent-1",
            message_content="test input",
        )
        result = agent.process_message(req, "public")
        assert result.message_role == "assistant"
        assert "Echo: test input" in result.message_content
        assert result.agent_id == "agent-1"
        utils.task_notification_service.publish_update.assert_called_once()
