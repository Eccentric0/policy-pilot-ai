from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from math import sqrt
from typing import Any


class EmbeddingProvider:
    """Create fixed-size vectors without making the demo depend on an API.

    The hash provider is deterministic and works well enough for the small
    Chinese policy corpus used by this project. In production, set
    EMBEDDING_PROVIDER=openai and provide an OpenAI-compatible embeddings API.
    """

    def __init__(
        self,
        provider: str = "hash",
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "",
        dimension: int = 1536,
    ):
        self.provider = provider.lower()
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        if self.provider == "openai":
            return self._embed_openai(text)
        return self._embed_hash(text)

    def _embed_hash(self, text: str) -> list[float]:
        # Character n-grams preserve useful overlap for Chinese text while
        # remaining deterministic and dependency-free.
        normalized = " ".join(text.lower().split())
        features = [normalized[i : i + 2] for i in range(max(0, len(normalized) - 1))]
        features += normalized.split()
        vector = [0.0] * self.dimension
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:8], "big") % self.dimension
            sign = 1.0 if digest[8] & 1 else -1.0
            vector[index] += sign
        norm = sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector

    def _embed_openai(self, text: str) -> list[float]:
        if not self.api_key or not self.model:
            raise RuntimeError("OPENAI_API_KEY 和 EMBEDDING_MODEL 必须同时配置")
        payload = json.dumps({"model": self.model, "input": text}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/embeddings",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body: dict[str, Any] = json.loads(response.read().decode("utf-8"))
            vector = [float(value) for value in body["data"][0]["embedding"]]
        except (urllib.error.URLError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Embedding 调用失败: {exc}") from exc
        if len(vector) != self.dimension:
            raise RuntimeError(
                f"Embedding 维度为 {len(vector)}，但数据库向量列要求 {self.dimension}；"
                "请调整 EMBEDDING_DIMENSION 并重建 document_chunks 表"
            )
        return vector


def vector_literal(vector: list[float]) -> str:
    """Format a vector for psycopg's parameterized ::vector cast."""
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"
