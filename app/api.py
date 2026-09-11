from __future__ import annotations

from typing import Any
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse
except ImportError:  # pragma: no cover
    FastAPI = None

from app.config import settings
from app.service import AgentService


service = AgentService(settings)

if FastAPI:
    app = FastAPI(title="企业制度与报销助手", version="0.1.0")
    web_dir = Path(__file__).parent / "static"

    @app.get("/", include_in_schema=False)
    def web_home():
        return FileResponse(web_dir / "index.html")

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "storage_backend": settings.storage_backend,
            "indexed_chunks": service.index.count(),
        }

    @app.post("/v1/chat")
    def chat(payload: dict[str, Any]) -> dict[str, Any]:
        if not payload.get("message"):
            raise HTTPException(status_code=422, detail="message 不能为空")
        state = service.chat(
            str(payload["message"]),
            str(payload.get("session_id", "default-session")),
            str(payload.get("user_id", "E1001")),
        )
        return {
            "run_id": state.run_id,
            "answer": state.answer,
            "citations": state.citations,
            "tool_calls": state.tool_calls,
            "status": state.status,
            "metrics": state.metrics,
        }

    @app.post("/v1/documents/reindex")
    def reindex() -> dict[str, Any]:
        return {"indexed_chunks": service.ingest()}

    @app.get("/v1/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        state = service.store.get(run_id)
        if not state:
            raise HTTPException(status_code=404, detail="run 不存在")
        return state.to_dict()

    @app.post("/v1/runs/{run_id}/approve")
    def approve(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        state = service.approve(run_id, bool(payload.get("approved", False)))
        if not state:
            raise HTTPException(status_code=404, detail="run 不存在")
        return state.to_dict()
else:
    app = None
