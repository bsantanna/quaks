from unittest.mock import MagicMock
import pytest
from app.domain.repositories.language_models import LanguageModelRepository, LanguageModelNotFoundError, LanguageModelSettingRepository
from app.domain.models import LanguageModel, LanguageModelSetting

@pytest.fixture
def mock_db():
    db = MagicMock()
    session = MagicMock()
    db.session.return_value.__enter__.return_value = session
    return db, session

@pytest.fixture
def lm_repository(mock_db):
    db, _ = mock_db
    return LanguageModelRepository(db=db)

@pytest.fixture
def lms_repository(mock_db):
    db, _ = mock_db
    return LanguageModelSettingRepository(db=db)

def test_get_all_lms(lm_repository, mock_db):
    db, session = mock_db
    schema = "schema-1"
    expected = [LanguageModel(id="1", language_model_tag="tag")]
    session.query.return_value.filter.return_value.all.return_value = expected

    result = lm_repository.get_all(schema)

    assert result == expected

def test_get_lm_by_id_success(lm_repository, mock_db):
    db, session = mock_db
    lm_id = "1"
    expected = LanguageModel(id=lm_id, language_model_tag="tag")
    session.query.return_value.filter.return_value.first.return_value = expected

    result = lm_repository.get_by_id(lm_id, "schema")

    assert result == expected

def test_add_lm(lm_repository, mock_db):
    db, session = mock_db
    result = lm_repository.add("int-1", "tag", "schema")
    assert result.language_model_tag == "tag"
    session.add.assert_called_once()

def test_get_all_lms_settings(lms_repository, mock_db):
    db, session = mock_db
    expected = [LanguageModelSetting(id="1", setting_key="k")]
    session.query.return_value.filter.return_value.all.return_value = expected
    result = lms_repository.get_all("lm-1", "schema")
    assert result == expected

def test_add_lms_setting(lms_repository, mock_db):
    db, session = mock_db
    result = lms_repository.add("lm-1", "key", "value", "schema")
    assert result.setting_key == "key"
    session.add.assert_called_once()
