import json, tempfile
from pathlib import Path
from adverhire.cli import main
from adverhire.llm import ModelRole, MockLLM

def test_cli_inspect_writes_questions_json(monkeypatch):
    mock = MockLLM(responses={ModelRole.FLASH: [
        {"claims": [{"bullet": "优化缓存", "tech": ["redis"], "metric": "50", "source": "resume"}]},
    ], ModelRole.PRO: [
        {"traps": [{"claim_idx": 0, "wrong_preset": "改成1800", "question": "怎么调的？", "discriminators": ["纠正"]}]},
    ]})
    monkeypatch.setattr("adverhire.cli.build_machine", lambda: __import__("adverhire.machine", fromlist=["AdversarialStateMachine"]).AdversarialStateMachine(mock))
    d = Path(tempfile.mkdtemp())
    resume = d / "r.md"; resume.write_text("# 简历")
    out = d / "q.json"
    code = main(["inspect", str(resume), "-o", str(out)])
    assert code == 0 and out.exists()
    data = json.loads(out.read_text())
    assert data["questions"][0]["question"]
