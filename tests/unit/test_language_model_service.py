from unittest.mock import MagicMock
import pytest
from app.services.language_models import LanguageModelService
from app.domain.models import LanguageModel, Integration

@pytest.fixture
def mock_lm_repo():
    return MagicMock()

@pytest.fixture
def mock_lms_service():
    return MagicMock()

@pytest.fixture
def mock_integration_service():
    return MagicMock()

@pytest.fixture
def service(mock_lm_repo, mock_lms_service, mock_integration_service):
    return LanguageModelService(
        language_model_repository=mock_lm_repo,
        language_model_setting_service=mock_lms_service,
        integration_service=mock_integration_service
    )

def test_get_language_models(service, mock_lm_repo):
    expected = [LanguageModel(id="1")]
    mock_lm_repo.get_all.return_value = expected
    assert service.get_language_models("schema") == expected

def test_get_language_model_by_id(service, mock_lm_repo):
    expected = LanguageModel(id="1")
    mock_lm_repo.get_by_id.return_value = expected
    assert service.get_language_model_by_id("1", "schema") == expected

def test_create_language_model_openai(service, mock_lm_repo, mock_lms_service, mock_integration_service):
    schema = "schema-1"
    integration = Integration(id="int-1", integration_type="openai_api_v1")
    mock_integration_service.get_integration_by_id.return_value = integration
    
    expected_lm = LanguageModel(id="lm-1", language_model_tag="tag")
    mock_lm_repo.add.return_value = expected_lm

    result = service.create_language_model("int-1", "tag", schema)

    assert result == expected_lm
    mock_lms_service.create_language_model_setting.assert_called_with(
        language_model_id="lm-1",
        setting_key="embeddings",
        setting_value="text-embedding-3-large",
        schema=schema
    )

def test_create_language_model_other(service, mock_lm_repo, mock_lms_service, mock_integration_service):
    schema = "schema-1"
    integration = Integration(id="int-1", integration_type="other")
    mock_integration_service.get_integration_by_id.return_value = integration
    
    expected_lm = LanguageModel(id="lm-1", language_model_tag="tag")
    mock_lm_repo.add.return_value = expected_lm

    result = service.create_language_model("int-1", "tag", schema)

    assert result == expected_lm
    mock_lms_service.create_language_model_setting.assert_called_with(
        language_model_id="lm-1",
        setting_key="embeddings",
        setting_value="bge-m3",
        schema=schema
    )

def test_delete_language_model_by_id(service, mock_lm_repo):
    service.delete_language_model_by_id("1", "schema")
    mock_lm_repo.delete_by_id.assert_called_once_with("1", "schema")

def test_update_language_model(service, mock_lm_repo, mock_integration_service):
    integration = Integration(id="int-1")
    mock_integration_service.get_integration_by_id.return_value = integration
    
    expected_lm = LanguageModel(id="1")
    mock_lm_repo.update_language_model.return_value = expected_lm
    
    result = service.update_language_model("1", "tag", "int-1", "schema")
    assert result == expected_lm
