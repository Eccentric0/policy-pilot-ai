from pathlib import Path

from app.retrieval.index import LocalIndex, build_local_index


def test_markdown_retrieval(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "policy.md").write_text("员工应在费用发生后30个自然日内提交报销申请。", encoding="utf-8")
    index = build_local_index(data, tmp_path / "index.json")
    results = index.search("报销提交时间", 3)
    assert results
    assert results[0]["source"] == "policy.md"
