import json
from pathlib import Path
from adverhire.followup import classify_answer
from adverhire.models import ImpactedTrap, Claim

HERE = Path(__file__).parent / "fixtures"

def _load():
    real_a = json.loads((HERE / "real_answers.json").read_text())
    faked_a = json.loads((HERE / "faked_answers.json").read_text())
    return real_a, faked_a

def test_fixtures_are_loadable_and_distinguishable():
    real_a, faked_a = _load()
    assert len(real_a) == len(faked_a) == 3
    trap = ImpactedTrap(Claim("优化缓存", ["redis"], 50.0, "resume"),
                        wrong_preset="P99降到260", question="怎么从820降到260的？",
                        discriminators=["其实", "回滚", "踩", "折腾"])
    # 真人回答含具身信号 -> 至少一条被判 corrected/vague；AI 回答 -> echoed/泛化
    assert any(classify_answer(a, trap) == "corrected" for a in real_a)
    assert all(a != "" for a in faked_a)  # 非空，供后续 LLM 判别
