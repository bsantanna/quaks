from unittest.mock import MagicMock
import pytest
from app.services.agent_settings import AgentSettingService
from app.domain.models import AgentSetting

@pytest.fixture
def mock_repository():
    return MagicMock()

@pytest.fixture
def service(mock_repository):
    return AgentSettingService(agent_setting_repository=mock_repository)

def test_get_agent_settings(service, mock_repository):
    agent_id = "agent-1"
    schema = "schema-1"
    expected_settings = [AgentSetting(id="1", agent_id=agent_id, setting_key="k", setting_value="v")]
    mock_repository.get_all.return_value = expected_settings

    result = service.get_agent_settings(agent_id, schema)

    assert result == expected_settings
    mock_repository.get_all.assert_called_once_with(agent_id, schema)

def test_create_agent_setting(service, mock_repository):
    agent_id = "agent-1"
    setting_key = "key"
    setting_value = "value"
    schema = "schema-1"
    expected_setting = AgentSetting(id="1", agent_id=agent_id, setting_key=setting_key, setting_value=setting_value)
    mock_repository.add.return_value = expected_setting

    result = service.create_agent_setting(agent_id, setting_key, setting_value, schema)

    assert result == expected_setting
    mock_repository.add.assert_called_once_with(
        agent_id=agent_id,
        setting_key=setting_key,
        setting_value=setting_value,
        schema=schema,
    )

def test_update_by_key(service, mock_repository):
    agent_id = "agent-1"
    setting_key = "key"
    setting_value = "new-value"
    schema = "schema-1"
    expected_setting = AgentSetting(id="1", agent_id=agent_id, setting_key=setting_key, setting_value=setting_value)
    mock_repository.update_by_key.return_value = expected_setting

    result = service.update_by_key(agent_id, setting_key, setting_value, schema)

    assert result == expected_setting
    mock_repository.update_by_key.assert_called_once_with(
        agent_id=agent_id,
        setting_key=setting_key,
        setting_value=setting_value,
        schema=schema,
    )
