from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dependency is optional at import time
    pass


_MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "mock").lower()
_DEFAULT_API_KEY = os.getenv("DEEPSEEK_API_KEY", "") if _MODEL_PROVIDER == "deepseek" else ""
_DEFAULT_BASE_URL = "https://api.deepseek.com" if _MODEL_PROVIDER == "deepseek" else "https://api.openai.com/v1"
_DEFAULT_MODEL = "deepseek-v4-flash" if _MODEL_PROVIDER == "deepseek" else ""


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "enterprise-expense-agent")
    model_provider: str = _MODEL_PROVIDER
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "") or _DEFAULT_API_KEY
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", _DEFAULT_BASE_URL)
    openai_model: str = os.getenv("OPENAI_MODEL", _DEFAULT_MODEL)
    storage_backend: str = os.getenv("STORAGE_BACKEND", "local")
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://agent:agent@localhost:5432/enterprise_agent"
    )
    data_dir: Path = Path(os.getenv("DATA_DIR", "data/policies"))
    runtime_dir: Path = Path(os.getenv("RUNTIME_DIR", "runtime"))
    max_steps: int = int(os.getenv("MAX_STEPS", "8"))
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "6"))
    tool_timeout_seconds: int = int(os.getenv("TOOL_TIMEOUT_SECONDS", "20"))
    mcp_mode: str = os.getenv("MCP_MODE", "local")
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "hash")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "")
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

    @property
    def index_path(self) -> Path:
        return self.runtime_dir / "index.json"

    @property
    def runs_dir(self) -> Path:
        return self.runtime_dir / "runs"


settings = Settings()
