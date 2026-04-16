import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import MessagesState

from app.domain.exceptions.base import ResourceNotFoundError
from app.services.agent_types.base import AgentUtils, WorkflowAgentBase


def _make_agent_utils(**overrides):
    defaults = dict(
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
    defaults.update(overrides)
    return AgentUtils(**defaults)


# Concrete subclass for testing non-abstract methods
class _StubWorkflowAgent(WorkflowAgentBase):
    def create_default_settings(self, agent_id, schema):
        pass

    def get_input_params(self, message_request, schema):
        return {}

    def get_workflow_builder(self, agent_id):
        return MagicMock()


class TestAgentBaseFormatResponse:
    def test_format_response(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        state = MessagesState(
            messages=[
                AIMessage(content="Hello"),
                AIMessage(content="World"),
            ]
        )
        content, data = agent.format_response(state)
        assert content == "World"
        assert "messages" in data
        assert len(data["messages"]) == 2


class TestAgentBaseGetLanguageModelIntegration:
    def test_returns_model_and_integration(self):
        mock_lm = MagicMock()
        mock_lm.integration_id = "int-1"
        mock_integration = MagicMock()

        utils = _make_agent_utils()
        utils.language_model_service.get_language_model_by_id.return_value = mock_lm
        utils.integration_service.get_integration_by_id.return_value = mock_integration

        agent = _StubWorkflowAgent(utils)
        mock_agent = MagicMock()
        mock_agent.language_model_id = "lm-1"

        lm, integ = agent.get_language_model_integration(mock_agent, "public")
        assert lm is mock_lm
        assert integ is mock_integration


class TestAgentBaseGetIntegrationCredentials:
    def test_returns_endpoint_and_key(self):
        utils = _make_agent_utils()
        utils.vault_client.secrets.kv.read_secret_version.return_value = {
            "data": {"data": {"api_endpoint": "https://api.example.com", "api_key": "key123"}}
        }
        agent = _StubWorkflowAgent(utils)
        integration = MagicMock()
        integration.id = "int-1"

        endpoint, key = agent.get_integration_credentials(integration)
        assert endpoint == "https://api.example.com"
        assert key == "key123"


class TestAgentBaseGetChatModel:
    def _setup_agent(self, integration_type):
        utils = _make_agent_utils()
        mock_agent_obj = MagicMock()
        mock_agent_obj.language_model_id = "lm-1"
        utils.agent_service.get_agent_by_id.return_value = mock_agent_obj

        mock_lm = MagicMock()
        mock_lm.integration_id = "int-1"
        mock_lm.language_model_tag = "test-model"
        utils.language_model_service.get_language_model_by_id.return_value = mock_lm

        mock_integration = MagicMock()
        mock_integration.id = "int-1"
        mock_integration.integration_type = integration_type
        utils.integration_service.get_integration_by_id.return_value = mock_integration

        utils.vault_client.secrets.kv.read_secret_version.return_value = {
            "data": {"data": {"api_endpoint": "http://localhost:11434", "api_key": "key"}}
        }
        return _StubWorkflowAgent(utils)

    def test_openai_type(self):
        agent = self._setup_agent("openai_api_v1")
        model = agent.get_chat_model("a1", "public")
        assert model is not None

    def test_anthropic_type(self):
        agent = self._setup_agent("anthropic_api_v1")
        model = agent.get_chat_model("a1", "public")
        assert model is not None

    def test_xai_type(self):
        agent = self._setup_agent("xai_api_v1")
        model = agent.get_chat_model("a1", "public")
        assert model is not None

    def test_ollama_default_type(self):
        agent = self._setup_agent("ollama_api_v1")
        model = agent.get_chat_model("a1", "public")
        assert model is not None

    def test_custom_language_model_tag(self):
        agent = self._setup_agent("openai_api_v1")
        model = agent.get_chat_model("a1", "public", language_model_tag="custom-tag")
        assert model is not None


class TestAgentBaseGetEmbeddingsModel:
    def _setup_agent(self, integration_type):
        utils = _make_agent_utils()
        mock_agent_obj = MagicMock()
        mock_agent_obj.language_model_id = "lm-1"
        utils.agent_service.get_agent_by_id.return_value = mock_agent_obj

        mock_lm = MagicMock()
        mock_lm.id = "lm-1"
        mock_lm.integration_id = "int-1"
        utils.language_model_service.get_language_model_by_id.return_value = mock_lm

        mock_integration = MagicMock()
        mock_integration.id = "int-1"
        mock_integration.integration_type = integration_type
        utils.integration_service.get_integration_by_id.return_value = mock_integration

        mock_setting = MagicMock()
        mock_setting.setting_key = "embeddings"
        mock_setting.setting_value = "text-embedding-ada-002"
        utils.language_model_setting_service.get_language_model_settings.return_value = [mock_setting]

        utils.vault_client.secrets.kv.read_secret_version.return_value = {
            "data": {"data": {"api_endpoint": "http://localhost:11434", "api_key": "key"}}
        }
        return _StubWorkflowAgent(utils)

    def test_openai_embeddings(self):
        agent = self._setup_agent("openai_api_v1")
        emb = agent.get_embeddings_model("a1", "public")
        assert emb is not None

    def test_ollama_embeddings(self):
        agent = self._setup_agent("ollama_api_v1")
        emb = agent.get_embeddings_model("a1", "public")
        assert emb is not None

    def test_default_embeddings(self):
        agent = self._setup_agent("unknown_type")
        with patch.dict(os.environ, {"OLLAMA_ENDPOINT": "http://localhost:11434"}):
            emb = agent.get_embeddings_model("a1", "public")
        assert emb is not None


class TestAgentBaseGetOpenaiClient:
    def test_returns_client(self):
        utils = _make_agent_utils()
        mock_agent_obj = MagicMock()
        mock_agent_obj.language_model_id = "lm-1"
        utils.agent_service.get_agent_by_id.return_value = mock_agent_obj

        mock_lm = MagicMock()
        mock_lm.integration_id = "int-1"
        utils.language_model_service.get_language_model_by_id.return_value = mock_lm

        mock_integration = MagicMock()
        mock_integration.id = "int-1"
        utils.integration_service.get_integration_by_id.return_value = mock_integration

        utils.vault_client.secrets.kv.read_secret_version.return_value = {
            "data": {"data": {"api_endpoint": "http://localhost:11434", "api_key": "key"}}
        }
        agent = _StubWorkflowAgent(utils)
        client = agent.get_openai_client("a1", "public")
        assert client is not None


class TestAgentBaseReadFileContent:
    def test_reads_existing_file(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("  hello world  ")
            f.flush()
            content = agent.read_file_content(f.name)
        os.unlink(f.name)
        assert content == "hello world"

    def test_raises_for_missing_file(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        with pytest.raises(ResourceNotFoundError):
            agent.read_file_content("/nonexistent/path.txt")


class TestAgentBaseParsePromptTemplate:
    def test_renders_template(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        settings = {"greeting": "Hello {{ name }}!"}
        result = agent.parse_prompt_template(settings, "greeting", {"name": "World"})
        assert result == "Hello World!"


class TestWorkflowAgentBaseGetConfig:
    def test_returns_config_dict(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        config = agent.get_config("agent-123")
        assert config["configurable"]["thread_id"] == "agent-123"
        assert config["recursion_limit"] == 30


class TestWorkflowAgentBaseCreateThoughtChain:
    def test_basic_thought_chain(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        result = agent.create_thought_chain("What is AI?", "AI is artificial intelligence.")
        assert "What is AI?" in result
        assert "AI is artificial intelligence." in result

    def test_thought_chain_with_connection(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        result = agent.create_thought_chain("Q", "A", connection="Related to ML")
        assert "Related to ML" in result

    def test_thought_chain_with_llm(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Summarized response")
        result = agent.create_thought_chain("Q", "Long answer", llm=mock_llm)
        assert "Summarized response" in result
        mock_llm.invoke.assert_called_once()


class TestClassifyShellToken:
    def test_pipe(self):
        ops = WorkflowAgentBase._REDIRECT_OPS
        assert WorkflowAgentBase._classify_shell_token("|", ops) == "pipe"

    def test_separator_semicolon(self):
        ops = WorkflowAgentBase._REDIRECT_OPS
        assert WorkflowAgentBase._classify_shell_token(";", ops) == "separator"

    def test_separator_and(self):
        ops = WorkflowAgentBase._REDIRECT_OPS
        assert WorkflowAgentBase._classify_shell_token("&&", ops) == "separator"

    def test_separator_or(self):
        ops = WorkflowAgentBase._REDIRECT_OPS
        assert WorkflowAgentBase._classify_shell_token("||", ops) == "separator"

    def test_redirection(self):
        ops = WorkflowAgentBase._REDIRECT_OPS
        assert WorkflowAgentBase._classify_shell_token(">", ops) == "redirection"
        assert WorkflowAgentBase._classify_shell_token("2>", ops) == "redirection"

    def test_variable(self):
        ops = WorkflowAgentBase._REDIRECT_OPS
        assert WorkflowAgentBase._classify_shell_token("FOO=bar", ops) == "variable"

    def test_subshell(self):
        ops = WorkflowAgentBase._REDIRECT_OPS
        assert WorkflowAgentBase._classify_shell_token("$(echo hi)", ops) == "subshell"
        assert WorkflowAgentBase._classify_shell_token("`echo hi`", ops) == "subshell"

    def test_command(self):
        ops = WorkflowAgentBase._REDIRECT_OPS
        assert WorkflowAgentBase._classify_shell_token("ls", ops) == "command"
        assert WorkflowAgentBase._classify_shell_token("-la", ops) == "command"


class TestAnalyzeShell:
    def test_simple_command(self):
        result, error = WorkflowAgentBase._analyze_shell("ls -la")
        assert error is None
        assert result["commands"] == ["ls -la"]
        assert result["pipes"] == 0

    def test_piped_commands(self):
        result, error = WorkflowAgentBase._analyze_shell("ls | grep foo")
        assert error is None
        assert result["pipes"] == 1
        assert len(result["commands"]) == 2

    def test_redirections(self):
        result, error = WorkflowAgentBase._analyze_shell("echo hello > out.txt")
        assert error is None
        assert ">" in result["redirections"]

    def test_variables(self):
        result, error = WorkflowAgentBase._analyze_shell("FOO=bar echo test")
        assert error is None
        assert "FOO" in result["variables"]

    def test_chained_commands(self):
        result, error = WorkflowAgentBase._analyze_shell("cmd1 && cmd2")
        assert error is None
        assert len(result["commands"]) == 2

    def test_parse_error(self):
        result, error = WorkflowAgentBase._analyze_shell("echo 'unterminated")
        assert result is None
        assert error is not None


class TestGetBashTool:
    def test_returns_tool(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        tool = agent.get_bash_tool()
        assert tool.name == "bash_tool"

    def test_tool_analyzes_valid_script(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        tool = agent.get_bash_tool()
        result = tool.invoke("ls -la | grep test")
        assert "Syntax: valid" in result
        assert "Pipes: 1" in result

    def test_tool_handles_parse_error(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        tool = agent.get_bash_tool()
        result = tool.invoke("echo 'unterminated")
        assert "Parse error" in result

    def test_tool_handles_non_string_input(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        tool = agent.get_bash_tool()
        result = tool.invoke({"cmd": 123})
        assert "Error analyzing script" in result


class TestGetLastInteractionMessages:
    def test_returns_last_interaction(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        msgs = [
            HumanMessage(content="first"),
            AIMessage(content="resp1"),
            HumanMessage(content="second"),
            AIMessage(content="resp2"),
        ]
        result = agent.get_last_interaction_messages(msgs)
        assert len(result) == 2
        assert result[0].content == "second"
        assert result[1].content == "resp2"

    def test_returns_empty_if_no_human_message(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        msgs = [AIMessage(content="resp")]
        result = agent.get_last_interaction_messages(msgs)
        assert result == []

    def test_returns_empty_for_empty_list(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        result = agent.get_last_interaction_messages([])
        assert result == []


class TestGetImageAnalysisChain:
    def test_returns_chain(self):
        utils = _make_agent_utils()
        agent = _StubWorkflowAgent(utils)
        mock_llm = MagicMock()
        chain = agent.get_image_analysis_chain(mock_llm, "Analyze this image", "image/png")
        assert chain is not None
