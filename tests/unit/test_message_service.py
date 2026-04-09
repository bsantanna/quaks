from unittest.mock import MagicMock
import pytest
from app.services.messages import MessageService
from app.domain.models import Message, Agent
from app.domain.repositories.agents import AgentNotFoundError
from app.domain.exceptions.base import InvalidFieldError

@pytest.fixture
def mock_message_repository():
    return MagicMock()

@pytest.fixture
def mock_agent_service():
    return MagicMock()

@pytest.fixture
def mock_attachment_service():
    return MagicMock()

@pytest.fixture
def service(mock_message_repository, mock_agent_service, mock_attachment_service):
    return MessageService(
        message_repository=mock_message_repository,
        agent_service=mock_agent_service,
        attachment_service=mock_attachment_service
    )

def test_get_messages(service, mock_message_repository, mock_agent_service):
    agent_id = "agent-1"
    schema = "schema-1"
    mock_agent = MagicMock(spec=Agent)
    mock_agent.id = agent_id
    mock_agent_service.get_agent_by_id.return_value = mock_agent
    
    expected_messages = [Message(id="1", message_role="human", message_content="hi", agent_id=agent_id)]
    mock_message_repository.get_all.return_value = expected_messages

    result = service.get_messages(agent_id, schema)

    assert result == expected_messages
    mock_agent_service.get_agent_by_id.assert_called_once_with(agent_id, schema)
    mock_message_repository.get_all.assert_called_once_with(agent_id, schema)

def test_get_message_by_id(service, mock_message_repository):
    message_id = "msg-1"
    schema = "schema-1"
    expected_message = Message(id=message_id, message_role="human", message_content="hi", agent_id="a1")
    mock_message_repository.get_by_id.return_value = expected_message

    result = service.get_message_by_id(message_id, schema)

    assert result == expected_message
    mock_message_repository.get_by_id.assert_called_once_with(message_id, schema)

def test_create_message_success(service, mock_message_repository, mock_agent_service):
    role = "human"
    content = "hi"
    agent_id = "agent-1"
    schema = "schema-1"
    
    mock_agent = MagicMock(spec=Agent)
    mock_agent_service.get_agent_by_id.return_value = mock_agent
    
    expected_message = Message(id="msg-1", message_role=role, message_content=content, agent_id=agent_id)
    mock_message_repository.add.return_value = expected_message

    result = service.create_message(role, content, agent_id, schema)

    assert result == expected_message
    mock_agent_service.get_agent_by_id.assert_called_once_with(agent_id, schema)
    mock_message_repository.add.assert_called_once_with(
        message_role=role,
        message_content=content,
        agent_id=agent_id,
        schema=schema,
        response_data=None,
        attachment_id=None,
        replies_to=None,
    )

def test_create_message_agent_not_found(service, mock_agent_service):
    agent_id = "invalid"
    mock_agent_service.get_agent_by_id.side_effect = AgentNotFoundError(agent_id)
    
    with pytest.raises(InvalidFieldError) as excinfo:
        service.create_message("human", "hi", agent_id, "schema")
    
    assert "agent_id" in excinfo.value.detail
    assert "agent not found" in excinfo.value.detail

def test_delete_message_by_id_with_reply(service, mock_message_repository):
    message_id = "msg-1"
    replies_to_id = "msg-reply-to"
    schema = "schema-1"
    
    mock_message = MagicMock(spec=Message)
    mock_message.replies_to = replies_to_id
    mock_message_repository.get_by_id.return_value = mock_message
    
    service.delete_message_by_id(message_id, schema)

    mock_message_repository.delete_by_id.assert_any_call(replies_to_id, schema)
    mock_message_repository.delete_by_id.assert_any_call(message_id, schema)
    assert mock_message_repository.delete_by_id.call_count == 2
