from unittest.mock import MagicMock, patch
import pytest
from app.services.tasks import TaskNotificationService, TaskProgress

@pytest.fixture
def mock_redis():
    with patch("redis.StrictRedis.from_url") as mock_from_url:
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        yield mock_client

@pytest.fixture
def service(mock_redis):
    return TaskNotificationService(redis_url="redis://localhost")

def test_publish_update(service, mock_redis):
    progress = TaskProgress(agent_id="agent-1", status="completed")
    service.publish_update(progress)
    
    mock_redis.publish.assert_called_once()
    assert "agent-1" in mock_redis.publish.call_args[0][1]
    assert "completed" in mock_redis.publish.call_args[0][1]

def test_subscribe(service, mock_redis):
    service.subscribe()
    mock_redis.pubsub.return_value.subscribe.assert_called_once_with("task_updates")

def test_listen(service, mock_redis):
    mock_redis.pubsub.return_value.listen.return_value = ["msg1", "msg2"]
    service.subscribe()
    messages = list(service.listen())
    assert messages == ["msg1", "msg2"]

def test_close(service, mock_redis):
    service.close()
    mock_redis.pubsub.return_value.unsubscribe.assert_called_once()
    mock_redis.pubsub.return_value.close.assert_called_once()
    mock_redis.close.assert_called_once()
