from app.llm import OpenAICompatibleClient
from app.config import Settings
from app.graph.workflow import run_workflow
from app.retrieval.index import build_local_index


def test_llm_disabled_without_credentials():
    client = OpenAICompatibleClient("", "https://api.deepseek.com", "deepseek-v4-flash")
    assert client.enabled is False


def test_workflow_falls_back_when_llm_endpoint_fails(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "policy.md").write_text("员工可以查询本人剩余年假。", encoding="utf-8")
    index = build_local_index(data, tmp_path / "index.json")
    config = Settings(
        data_dir=data,
        runtime_dir=tmp_path / "runtime",
        openai_api_key="test-key",
        openai_base_url="http://127.0.0.1:1/v1",
        openai_model="deepseek-v4-flash",
        llm_timeout_seconds=1,
    )
    state = run_workflow("E1001还剩多少年假？", "fallback-session", "E1001", index, config)
    assert state.status == "completed"
    assert "6" in state.answer
