"""测试薄驱动脚本 scripts/verify.py。

用可注入的 MockLLM 响应确定性驱动 pipeline，断言：
- probe：坑题都绑定真实 claim，非 claimable 的 claim 不产生坑题。
- review：产出结构化 RiskReport，by_dimension 五维齐全、均为 float。
- 不变量 #2：overall 只可能是 LOW/MEDIUM/HIGH，报告不含淘汰/录用结论。
- 判别性机制：配置更高虚构成分(faked) 的 review 风险 > 配置更低(real)。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "tests" / "fixtures"
RESP = FIX / "responses"


def _run(*argv: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "verify.py"), *argv],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert proc.returncode == 0, f"非零退出: {proc.stderr}"
    return json.loads(proc.stdout)


def test_probe_binds_questions_to_claims_and_skips_unclaimable():
    out = _run("probe", str(FIX / "real.md"), "--mock",
               "--responses", str(RESP / "mock_probe.json"))
    claims = out["claims"]
    # 三个 claim 中前两个 claimable，第三个（纯软技能，无 tech/metric）不 claimable
    questions = out["questions"]
    assert len(questions) == 2
    for q in questions:
        assert 0 <= q["claim_idx"] < len(claims)
        assert q["claim"] == claims[q["claim_idx"]]["bullet"]  # 绑定真实 claim
    # 非 claimable 的不出坑题
    assert all(q["claim"] != "纯软技能" for q in questions)


def test_review_report_structure_and_invariant2():
    out = _run("review", str(FIX / "real.md"), str(FIX / "real_answers.json"),
               "--mock", "--responses", str(RESP / "mock_review_real.json"))
    report = out["report"]
    assert report["overall"] in {"LOW", "MEDIUM", "HIGH"}
    # 五维齐全、均为 float
    dims = report["by_dimension"]
    assert set(dims) == {"template_cliche", "no_embodied_detail", "over_generalization",
                         "missing_affect", "over_standardized"}
    assert all(isinstance(v, float) for v in dims.values())
    # 不变量 #2：绝不输出淘汰/录用结论
    text = json.dumps(report, ensure_ascii=False)
    assert "淘汰" not in text and "录用" not in text


def test_review_discriminability_faked_ranks_higher_than_real():
    real = _run("review", str(FIX / "real.md"), str(FIX / "real_answers.json"),
                "--mock", "--responses", str(RESP / "mock_review_real.json"))
    faked = _run("review", str(FIX / "faked.md"), str(FIX / "faked_answers.json"),
                 "--mock", "--responses", str(RESP / "mock_review_faked.json"))
    # 配置更高虚构成分的 faked => 信号更多、overall 风险更高
    assert len(faked["report"]["signals"]) > len(real["report"]["signals"])
    risk_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    assert risk_rank[faked["report"]["overall"]] > risk_rank[real["report"]["overall"]]
