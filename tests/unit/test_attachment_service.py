from unittest.mock import MagicMock, patch

import pytest

from app.domain.models import Attachment
from app.services.attachments import AttachmentService


@pytest.fixture
def mock_deps():
    return {
        "attachment_repository": MagicMock(),
        "document_repository": MagicMock(),
        "language_model_service": MagicMock(),
        "language_model_setting_service": MagicMock(),
        "integration_service": MagicMock(),
        "vault_client": MagicMock(),
    }


@pytest.fixture
def service(mock_deps):
    return AttachmentService(**mock_deps)


def _make_attachment(**kwargs):
    defaults = {
        "id": "att-1",
        "is_active": True,
        "file_name": "test.pdf",
        "raw_content": b"raw",
        "parsed_content": "parsed text",
    }
    defaults.update(kwargs)
    att = MagicMock(spec=Attachment)
    for k, v in defaults.items():
        setattr(att, k, v)
    return att


class TestGetAttachments:
    def test_returns_all_attachments(self, service, mock_deps):
        expected = [_make_attachment(), _make_attachment(id="att-2")]
        mock_deps["attachment_repository"].get_all.return_value = expected

        result = service.get_attachments("public")

        mock_deps["attachment_repository"].get_all.assert_called_once_with("public")
        assert result == expected

    def test_get_attachment_by_id(self, service, mock_deps):
        expected = _make_attachment()
        mock_deps["attachment_repository"].get_by_id.return_value = expected

        result = service.get_attachment_by_id("att-1", "public")

        mock_deps["attachment_repository"].get_by_id.assert_called_once_with(
            "att-1", "public"
        )
        assert result == expected


class TestDeleteAttachment:
    def test_delegates_to_repository(self, service, mock_deps):
        service.delete_attachment_by_id("att-1", "public")

        mock_deps["attachment_repository"].delete_by_id.assert_called_once_with(
            "att-1", "public"
        )


class TestCreateAttachmentWithContent:
    def test_delegates_to_repository(self, service, mock_deps):
        expected = _make_attachment()
        mock_deps["attachment_repository"].add.return_value = expected

        result = service.create_attachment_with_content(
            file_name="test.pdf",
            raw_content=b"raw",
            parsed_content="parsed",
            schema="public",
        )

        mock_deps["attachment_repository"].add.assert_called_once_with(
            file_name="test.pdf",
            raw_content=b"raw",
            parsed_content="parsed",
            attachment_id=None,
            schema="public",
        )
        assert result == expected

    def test_passes_attachment_id_when_provided(self, service, mock_deps):
        mock_deps["attachment_repository"].add.return_value = _make_attachment()

        service.create_attachment_with_content(
            file_name="test.pdf",
            raw_content=b"raw",
            parsed_content="parsed",
            schema="public",
            attachment_id="custom-id",
        )

        mock_deps["attachment_repository"].add.assert_called_once_with(
            file_name="test.pdf",
            raw_content=b"raw",
            parsed_content="parsed",
            attachment_id="custom-id",
            schema="public",
        )


class TestOptimizeAudio:
    @patch("app.services.attachments.subprocess.run")
    def test_calls_ffmpeg_and_returns_bytes(self, mock_run, service):
        test_audio = b"optimized audio content"

        mock_open = MagicMock()
        mock_open.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=test_audio)))
        mock_open.__exit__ = MagicMock(return_value=False)

        with patch("builtins.open", return_value=mock_open):
            result = service.optimize_audio("/tmp/test.wav")

        assert mock_run.call_count == 2
        first_call = mock_run.call_args_list[0]
        assert first_call[0][0][0] == "ffmpeg"
        assert "-b:a" in first_call[0][0]
        assert "64k" in first_call[0][0]
        assert result == test_audio

    @patch("app.services.attachments.subprocess.run")
    def test_raises_on_ffmpeg_failure(self, mock_run, service):
        from subprocess import CalledProcessError

        from app.domain.exceptions.base import AudioOptimizationError

        mock_run.side_effect = CalledProcessError(1, "ffmpeg")

        with pytest.raises(AudioOptimizationError):
            service.optimize_audio("/tmp/test.wav")
