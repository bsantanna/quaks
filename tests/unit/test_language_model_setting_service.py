from unittest.mock import MagicMock
import pytest
from app.services.language_model_settings import LanguageModelSettingService
from app.domain.models import LanguageModelSetting

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def service(mock_repo):
    return LanguageModelSettingService(language_model_setting_repository=mock_repo)

def test_get_language_model_settings(service, mock_repo):
    expected = [LanguageModelSetting(id="1")]
    mock_repo.get_all.return_value = expected
    assert service.get_language_model_settings("lm-1", "schema") == expected

def test_create_language_model_setting(service, mock_repo):
    expected = LanguageModelSetting(id="1")
    mock_repo.add.return_value = expected
    assert service.create_language_model_setting("lm-1", "key", "val", "schema") == expected

def test_update_by_key(service, mock_repo):
    expected = LanguageModelSetting(id="1")
    mock_repo.update_by_key.return_value = expected
    assert service.update_by_key("lm-1", "key", "val", "schema") == expected
