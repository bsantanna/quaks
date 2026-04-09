from unittest.mock import MagicMock
import pytest
from app.services.agents import AgentService
from app.domain.models import Agent, LanguageModel

@pytest.fixture
def mock_agent_repository():
    return MagicMock()

@pytest.fixture
def mock_agent_setting_service():
    return MagicMock()

@pytest.fixture
def mock_language_model_service():
    return MagicMock()

@pytest.fixture
def service(mock_agent_repository, mock_agent_setting_service, mock_language_model_service):
    return AgentService(
        agent_repository=mock_agent_repository,
        agent_setting_service=mock_agent_setting_service,
        language_model_service=mock_language_model_service
    )

def test_get_agents(service, mock_agent_repository):
    schema = "schema-1"
    expected_agents = [Agent(id="1", agent_name="Agent 1", agent_type="type", language_model_id="lm-1")]
    mock_agent_repository.get_all.return_value = expected_agents

    result = service.get_agents(schema)

    assert result == expected_agents
    mock_agent_repository.get_all.assert_called_once_with(schema)

def test_get_agent_by_id(service, mock_agent_repository):
    agent_id = "agent-1"
    schema = "schema-1"
    expected_agent = Agent(id=agent_id, agent_name="Agent 1", agent_type="type", language_model_id="lm-1")
    mock_agent_repository.get_by_id.return_value = expected_agent

    result = service.get_agent_by_id(agent_id, schema)

    assert result == expected_agent
    mock_agent_repository.get_by_id.assert_called_once_with(agent_id, schema)

def test_create_agent(service, mock_agent_repository, mock_language_model_service):
    agent_name = "New Agent"
    agent_type = "type"
    language_model_id = "lm-1"
    schema = "schema-1"
    
    mock_lm = MagicMock(spec=LanguageModel)
    mock_lm.id = language_model_id
    mock_language_model_service.get_language_model_by_id.return_value = mock_lm
    
    expected_agent = Agent(id="agent-1", agent_name=agent_name, agent_type=agent_type, language_model_id=language_model_id)
    mock_agent_repository.add.return_value = expected_agent

    result = service.create_agent(agent_name, agent_type, language_model_id, schema)

    assert result == expected_agent
    mock_language_model_service.get_language_model_by_id.assert_called_once_with(language_model_id, schema)
    mock_agent_repository.add.assert_called_once_with(
        agent_name=agent_name,
        agent_type=agent_type,
        language_model_id=language_model_id,
        schema=schema,
    )

def test_delete_agent_by_id(service, mock_agent_repository):
    agent_id = "agent-1"
    schema = "schema-1"
    
    service.delete_agent_by_id(agent_id, schema)

    mock_agent_repository.delete_by_id.assert_called_once_with(agent_id, schema)

def test_update_agent(service, mock_agent_repository, mock_language_model_service):
    agent_id = "agent-1"
    agent_name = "Updated Agent"
    language_model_id = "lm-2"
    agent_summary = "summary"
    schema = "schema-1"
    
    mock_lm = MagicMock(spec=LanguageModel)
    mock_lm.id = language_model_id
    mock_language_model_service.get_language_model_by_id.return_value = mock_lm
    
    expected_agent = Agent(id=agent_id, agent_name=agent_name, agent_type="type", language_model_id=language_model_id)
    mock_agent_repository.update_agent.return_value = expected_agent

    result = service.update_agent(agent_id, agent_name, language_model_id, schema, agent_summary)

    assert result == expected_agent
    mock_language_model_service.get_language_model_by_id.assert_called_once_with(language_model_id, schema)
    mock_agent_repository.update_agent.assert_called_once_with(
        agent_id=agent_id,
        agent_name=agent_name,
        language_model_id=language_model_id,
        agent_summary=agent_summary,
        schema=schema,
    )
