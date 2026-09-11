from __future__ import annotations

from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from app.retrieval.embeddings import EmbeddingProvider, vector_literal
from app.retrieval.index import DocumentChunk, load_chunks


SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    page INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS document_chunks_source_idx ON document_chunks(source);
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx
    ON document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS agent_runs (
    run_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    status TEXT NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


class PostgresIndex:
    """PostgreSQL/pgvector backed document index."""

    def __init__(self, database_url: str, embedding_provider: EmbeddingProvider):
        self.database_url = database_url
        self.embedding_provider = embedding_provider
        self._ready = False

    def _connect(self):
        return psycopg.connect(self.database_url, connect_timeout=5)

    def ensure_schema(self) -> None:
        if self._ready:
            return
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(SCHEMA_SQL)
        self._ready = True

    def replace_from_directory(self, data_dir: Path) -> int:
        self.ensure_schema()
        chunks = load_chunks(data_dir)
        rows = [
            (
                chunk.chunk_id,
                chunk.source,
                chunk.page,
                chunk.content,
                vector_literal(self.embedding_provider.embed(chunk.content)),
                Jsonb({"source": chunk.source, "page": chunk.page}),
            )
            for chunk in chunks
        ]
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM document_chunks")
                if rows:
                    cursor.executemany(
                        """
                        INSERT INTO document_chunks
                            (id, source, page, content, embedding, metadata)
                        VALUES (%s, %s, %s, %s, %s::vector, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            source = EXCLUDED.source,
                            page = EXCLUDED.page,
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata
                        """,
                        rows,
                    )
        return len(chunks)

    def count(self) -> int:
        self.ensure_schema()
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM document_chunks")
                return int(cursor.fetchone()[0])

    def is_empty(self) -> bool:
        return self.count() == 0

    def search(self, query: str, top_k: int = 6) -> list[dict[str, Any]]:
        self.ensure_schema()
        query_vector = vector_literal(self.embedding_provider.embed(query))
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, source, page, content,
                           1 - (embedding <=> %s::vector) AS score
                    FROM document_chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_vector, query_vector, top_k),
                )
                rows = cursor.fetchall()
        return [
            {
                "chunk_id": row[0],
                "source": row[1],
                "page": row[2],
                "content": row[3],
                "score": round(max(0.0, float(row[4])), 4),
            }
            for row in rows
        ]


class PostgresRunStore:
    """Run persistence using the agent_runs JSONB state column."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._ready = False

    def ensure_schema(self) -> None:
        if self._ready:
            return
        with psycopg.connect(self.database_url, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute(SCHEMA_SQL)
        self._ready = True

    def save(self, state) -> None:
        self.ensure_schema()
        with psycopg.connect(self.database_url, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO agent_runs (run_id, session_id, status, state)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET
                        session_id = EXCLUDED.session_id,
                        status = EXCLUDED.status,
                        state = EXCLUDED.state,
                        updated_at = now()
                    """,
                    (state.run_id, state.session_id, state.status, Jsonb(state.to_dict())),
                )

    def get(self, run_id: str):
        from app.models import AgentState

        self.ensure_schema()
        with psycopg.connect(self.database_url, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT state FROM agent_runs WHERE run_id = %s", (run_id,))
                row = cursor.fetchone()
        return AgentState(**row[0]) if row else None
