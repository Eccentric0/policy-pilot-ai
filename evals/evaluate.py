from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.graph.workflow import classify_intent


def _load_cases() -> list[dict[str, Any]]:
    path = Path(__file__).with_name("dataset.jsonl")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_evaluation(service) -> dict[str, Any]:
    cases = _load_cases()
    results = []
    started = time.perf_counter()
    for case in cases:
        predicted_intent = classify_intent(case["question"])
        state = service.chat(case["question"], "eval-session", "E1001")
        tool_names = [item["name"] for item in state.tool_calls]
        results.append({
            "id": case["id"],
            "intent_correct": predicted_intent == case["expected_intent"],
            "source_correct": not case.get("expected_source") or any(case["expected_source"] == item["source"] for item in state.citations),
            "tool_correct": not case.get("expected_tool") or case["expected_tool"] in tool_names,
            "human_review_correct": bool(case.get("requires_human_review")) == state.need_human_review,
            "status": state.status,
        })
    def rate(key: str) -> float:
        return round(sum(bool(item[key]) for item in results) / max(len(results), 1), 4)
    return {
        "cases": len(results),
        "intent_accuracy": rate("intent_correct"),
        "citation_source_accuracy": rate("source_correct"),
        "tool_selection_accuracy": rate("tool_correct"),
        "human_review_accuracy": rate("human_review_correct"),
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "results": results,
    }
