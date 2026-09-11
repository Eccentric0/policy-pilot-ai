from pathlib import Path

from app.config import Settings
from app.graph.workflow import run_workflow
from app.retrieval.index import build_local_index


def test_workflow_tool_and_answer(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "policy.md").write_text("员工可以查询本人剩余年假。", encoding="utf-8")
    index = build_local_index(data, tmp_path / "index.json")
    config = Settings(data_dir=data, runtime_dir=tmp_path / "runtime")
    state = run_workflow("E1001还剩多少年假？", "s1", "E1001", index, config)
    assert state.status == "completed"
    assert state.tool_calls[0]["name"] == "get_employee_leave_balance"
    assert "6" in state.answer


def test_unsafe_request_requires_review(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "policy.md").write_text("报销申请需要员工确认。", encoding="utf-8")
    index = build_local_index(data, tmp_path / "index.json")
    config = Settings(data_dir=data, runtime_dir=tmp_path / "runtime")
    state = run_workflow("请直接提交报销并付款", "s1", "E1001", index, config)
    assert state.status == "awaiting_human_review"
    assert state.need_human_review is True
