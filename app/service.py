from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.graph.workflow import run_workflow
from app.models import AgentState
from app.retrieval.embeddings import EmbeddingProvider
from app.retrieval.index import LocalIndex, build_local_index
from app.retrieval.postgres import PostgresIndex, PostgresRunStore
from app.storage import RunStore


class AgentService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.runtime_dir.mkdir(parents=True, exist_ok=True)
        if settings.storage_backend.lower() == "postgres":
            self.store = PostgresRunStore(settings.database_url)
        else:
            self.store = RunStore(settings.runs_dir)
        self.index = self._load_index()

    def _load_index(self):
        if self.settings.storage_backend.lower() == "postgres":
            return PostgresIndex(
                self.settings.database_url,
                EmbeddingProvider(
                    provider=self.settings.embedding_provider,
                    api_key=self.settings.openai_api_key,
                    base_url=self.settings.openai_base_url,
                    model=self.settings.embedding_model,
                    dimension=self.settings.embedding_dimension,
                ),
            )
        if self.settings.index_path.exists():
            return LocalIndex.load(self.settings.index_path)
        return LocalIndex([])

    def ingest(self) -> int:
        if isinstance(self.index, PostgresIndex):
            return self.index.replace_from_directory(self.settings.data_dir)
        self.index = build_local_index(self.settings.data_dir, self.settings.index_path)
        return len(self.index.chunks)

    def chat(self, question: str, session_id: str, user_id: str) -> AgentState:
        if self.index.is_empty():
            self.ingest()
        state = run_workflow(question, session_id, user_id, self.index, self.settings)
        self.store.save(state)
        return state

    def approve(self, run_id: str, approved: bool) -> AgentState | None:
        previous = self.store.get(run_id)
        if not previous:
            return None
        if not approved:
            previous.human_approved = False
            previous.status = "rejected"
            previous.answer = "人工审核未通过，未执行后续操作。"
            self.store.save(previous)
            return previous
        state = run_workflow(
            previous.question,
            previous.session_id,
            previous.user_id,
            self.index,
            self.settings,
            run_id=run_id,
            human_approved=True,
        )
        self.store.save(state)
        return state
