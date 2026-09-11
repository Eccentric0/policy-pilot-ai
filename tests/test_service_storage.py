from pathlib import Path

from app.config import Settings
from app.service import AgentService


def test_local_service_still_uses_fallback(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "policy.md").write_text("费用报销应在发生后提交。", encoding="utf-8")
    service = AgentService(Settings(data_dir=data, runtime_dir=tmp_path / "runtime"))
    assert service.ingest() == 1
    assert service.index.is_empty() is False
