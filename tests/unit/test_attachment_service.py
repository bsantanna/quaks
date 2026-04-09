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


class TestCreateAttachmentWithFile:
    @pytest.mark.asyncio
    @patch("app.services.attachments.MarkItDown")
    @patch("app.services.attachments.anyio.open_file")
    @patch("app.services.attachments.os.remove")
    async def test_creates_from_markdown(self, mock_remove, mock_open, mock_mid, service, mock_deps):
        from unittest.mock import AsyncMock
        mock_file = MagicMock()
        mock_file.filename = "test.md"
        mock_file.content_type = "text/markdown"
        mock_file.read = AsyncMock(return_value=b"markdown content")
        
        mock_mid_inst = mock_mid.return_value
        mock_mid_inst.convert.return_value.text_content = "parsed markdown"
        
        expected = _make_attachment(file_name="test.md", parsed_content="parsed markdown")
        mock_deps["attachment_repository"].add.return_value = expected
        
        # Mock anyio.open_file
        mock_buffer = MagicMock()
        mock_buffer.write = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_buffer

        result = await service.create_attachment_with_file(mock_file, "public")

        assert result == expected
        mock_deps["attachment_repository"].add.assert_called_once()
        mock_remove.assert_called_once()

class TestCreateEmbeddings:
    @pytest.mark.asyncio
    @patch("app.services.attachments.OpenAIEmbeddings")
    @patch("app.services.attachments.UnstructuredMarkdownLoader")
    @patch("app.services.attachments.CharacterTextSplitter")
    @patch("app.services.attachments.anyio.open_file")
    @patch("app.services.attachments.os.remove")
    async def test_creates_openai_embeddings(self, mock_remove, mock_open, mock_splitter, mock_loader, mock_openai, service, mock_deps):
        from unittest.mock import AsyncMock
        schema = "public"
        lm_id = "lm-1"
        att_id = "att-1"
        col_name = "collection"
        
        mock_deps["language_model_service"].get_language_model_by_id.return_value = MagicMock(id=lm_id, integration_id="int-1")
        mock_deps["language_model_setting_service"].get_language_model_settings.return_value = [
            MagicMock(setting_key="embeddings", setting_value="text-embedding-3-large")
        ]
        mock_deps["integration_service"].get_integration_by_id.return_value = MagicMock(id="int-1", integration_type="openai_api_v1")
        mock_deps["vault_client"].secrets.kv.read_secret_version.return_value = {
            "data": {"data": {"api_endpoint": "http://api", "api_key": "key"}}
        }
        
        att = _make_attachment(id=att_id, parsed_content="content")
        mock_deps["attachment_repository"].get_by_id.return_value = att
        
        mock_buffer = MagicMock()
        mock_buffer.write = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_buffer
        
        expected_updated = _make_attachment(id=att_id, embeddings_collection=col_name)
        mock_deps["attachment_repository"].update_attachment.return_value = expected_updated
        
        result = await service.create_embeddings(att_id, lm_id, col_name, schema)
        
        assert result == expected_updated
        mock_openai.assert_called_once()
        mock_deps["document_repository"].add.assert_called_once()
        mock_remove.assert_called_once()
