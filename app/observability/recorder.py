from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any


_SENSITIVE = re.compile(r"\b(?:E\d{4}|员工编号\s*[:：]?\s*\w+)\b", re.IGNORECASE)


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return _SENSITIVE.sub("[REDACTED_EMPLOYEE]", value)
    if isinstance(value, dict):
        return {str(k): redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


class RunRecorder:
    def __init__(self, runtime_dir: Path, run_id: str):
        self.run_id = run_id
        self.started = time.perf_counter()
        self.path = runtime_dir / "traces.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def event(self, name: str, payload: dict[str, Any] | None = None, **extra: Any) -> None:
        item = {
            "timestamp": time.time(),
            "run_id": self.run_id,
            "event": name,
            "elapsed_ms": round((time.perf_counter() - self.started) * 1000, 2),
            **redact(payload or {}),
            **redact(extra),
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")

    def node(self, name: str):
        return _NodeTimer(self, name)


class _NodeTimer:
    def __init__(self, recorder: RunRecorder, name: str):
        self.recorder = recorder
        self.name = name
        self.started = 0.0

    def __enter__(self):
        self.started = time.perf_counter()
        self.recorder.event("node_start", node=self.name)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.recorder.event(
            "node_end",
            node=self.name,
            success=exc_type is None,
            duration_ms=round((time.perf_counter() - self.started) * 1000, 2),
            error=str(exc_value) if exc_value else None,
        )
        return False
