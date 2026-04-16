from unittest.mock import MagicMock

from app.services.agent_types.base import join_messages, AgentUtils


class TestJoinMessages:
    def test_join_two_lists(self):
        result = join_messages(["a", "b"], ["c", "d"])
        assert result == ["a", "b", "c", "d"]

    def test_deduplicates(self):
        result = join_messages(["a", "b"], ["b", "c"])
        assert result == ["a", "b", "c"]

    def test_handles_non_list_left(self):
        result = join_messages("a", ["b"])
        assert result == ["a", "b"]

    def test_handles_non_list_right(self):
        result = join_messages(["a"], "b")
        assert result == ["a", "b"]

    def test_handles_both_non_list(self):
        result = join_messages("a", "b")
        assert result == ["a", "b"]

    def test_empty_lists(self):
        result = join_messages([], [])
        assert result == []

    def test_identical_messages(self):
        result = join_messages(["a", "a"], ["a"])
        assert result == ["a"]


class TestAgentUtils:
    def test_initialization(self):
        utils = AgentUtils(
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
        assert utils.agent_service is not None
        assert utils.config is not None
        assert utils.vault_client is not None
        assert utils.graph_persistence_factory is not None
        assert utils.document_repository is not None
        assert utils.task_notification_service is not None
