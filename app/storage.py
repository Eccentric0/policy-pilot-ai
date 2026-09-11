from __future__ import annotations

import json
from pathlib import Path

from app.models import AgentState


class RunStore:
    def __init__(self, runs_dir: Path):
        self.runs_dir = runs_dir
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: AgentState) -> None:
        (self.runs_dir / f"{state.run_id}.json").write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get(self, run_id: str) -> AgentState | None:
        path = self.runs_dir / f"{run_id}.json"
        if not path.exists():
            return None
        return AgentState(**json.loads(path.read_text(encoding="utf-8")))
