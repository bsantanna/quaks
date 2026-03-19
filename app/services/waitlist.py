import hashlib
from datetime import datetime, timezone

from elasticsearch import ConflictError, Elasticsearch

from app.domain.exceptions.base import DuplicateEntryError


class WaitlistService:
    INDEX_ALIAS = "quaks_waiting-list_latest"

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    def _dated_index(self) -> str:
        return f"quaks_waiting-list_{datetime.now(timezone.utc).strftime('%d_%m_%Y')}"

    def register(
        self, email: str, username: str, first_name: str, last_name: str
    ) -> None:
        doc_id = hashlib.sha256(email.encode()).hexdigest()
        doc = {
            "key_email": email,
            "key_username": username,
            "text_first_name": first_name,
            "text_last_name": last_name,
            "date_timestamp": datetime.now(timezone.utc).isoformat(),
            "flag_processed": False,
        }
        try:
            dated_index = self._dated_index()
            self.es.index(
                index=dated_index,
                id=doc_id,
                document=doc,
                op_type="create",
            )
            if not self.es.indices.exists_alias(
                index=dated_index, name=self.INDEX_ALIAS
            ):
                self.es.indices.put_alias(
                    index=dated_index, name=self.INDEX_ALIAS
                )
        except ConflictError:
            raise DuplicateEntryError("Email")
