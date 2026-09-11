from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Citation:
    source: str
    page: int
    snippet: str
    score: float = 0.0


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None = None
    duration_ms: float | None = None


@dataclass
class AgentState:
    run_id: str
    session_id: str
    user_id: str
    question: str
    normalized_question: str = ""
    intent: str = "UNSUPPORTED"
    retrieved_docs: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    answer: str = ""
    status: str = "running"
    need_human_review: bool = False
    human_approved: bool | None = None
    error: str | None = None
    steps: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def state_from_dict(value: dict[str, Any]) -> AgentState:
    return AgentState(**value)
