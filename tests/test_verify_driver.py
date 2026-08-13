"""测试薄驱动脚本 scripts/verify.py 的 subagent 接口（tactics/validate/review）。

用纯规则引擎跑通全链路，断言：
- tactics：输出坑题战术，绑定到不可验证断言过滤。
- validate：强制不变量 #1（越界/非 claimable/空题过滤）。
- review：输出结构化报告，五维浮点、风险分级、判别性纯规则成立。
全程零 LLM/Mock——这是确定性规则的回归保障。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "verify.py"


def _write_tmp(content) -> Path:
    f = Path(tempfile.mktemp(suffix=".json"))
    f.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    return f


def _run(*argv: str) -> dict:
    proc = subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 0, f"vexit: {proc.stderr}"
    return json.loads(proc.stdout)


def test_tactics_binds_to_claimable_only():
    claims = _write_tmp([
        {"bullet": "优化缓存QPS+50%", "tech": ["redis"], "metric": 50},
        {"bullet": "软技能", "tech": [], "metric": None},
    ])
    out = _run("tactics", "--claims", str(claims))
    assert len(out["claims"]) == 2
    # 两个战术都只针对可验证断言[0]
    assert len(out["tactics"]) >= 1
    assert all(t["claim_idx"] == 0 for t in out["tactics"])


def test_validate_filters_invariant1():
    claims = _write_tmp([
        {"bullet": "优化缓存", "tech": ["redis"], "metric": 50},
        {"bullet": "软技能", "tech": [], "metric": None},
    ])
    traps = _write_tmp([
        {"claim_idx": 0, "question": "怎么调的？", "wrong_preset": "p", "discriminators": []},
        {"claim_idx": 1, "question": "非claimable", "wrong_preset": "p", "discriminators": []},
        {"claim_idx": 99, "question": "越界", "wrong_preset": "p", "discriminators": []},
        {"claim_idx": 0, "question": "  ", "wrong_preset": "p", "discriminators": []},
    ])
    out = _run("validate", "--claims", str(claims), "--traps", str(traps))
    assert len(out["questions"]) == 1
    assert out["questions"][0]["question"] == "怎么调的？"


def test_review_discrimination_real_vs_faked_via_pure_rules():
    claims = _write_tmp([
        {"bullet": "优化缓存QPS+50%", "tech": ["redis"], "metric": 50},
    ])
    embodied = _write_tmp(["其实当时我们用了lua批量回源，回滚过一次才稳定下来"])
    vague = _write_tmp(["通过深度优化和先进算法显著提升性能，达到业界领先"])

    real = _run("review", "--claims", str(claims), "--answers", str(embodied),
                "--summary", "见真实细节")
    faked = _run("review", "--claims", str(claims), "--answers", str(vague),
                 "--summary", "疑似AI注水")

    rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    assert real["overall"] in rank and faked["overall"] in rank
    assert rank[faked["overall"]] > rank[real["overall"]]
    # 五维浮点齐全
    dims = faked["by_dimension"]
    assert set(dims) == {"template_cliche", "no_embodied_detail", "over_generalization",
                         "missing_affect", "over_standardized"}
    assert all(isinstance(v, float) for v in dims.values())
