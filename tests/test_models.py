from adverhire.models import RiskLevel, Claim, ImpactedTrap

def test_risk_level_enum_values():
    assert {rl.value for rl in RiskLevel} == {"LOW", "MEDIUM", "HIGH"}

def test_claim_defaults_and_source():
    c = Claim("优化缓存 QPS+50%", ["redis"], 50.0, "resume")
    assert c.metric == 50.0 and c.source == "resume"

def test_trap_carries_claim_and_discriminators():
    c = Claim("纯文本", [], None, "resume")
    t = ImpactedTrap(c, wrong_preset="改成1800", question="从200怎么调到1800的？",
                     discriminators=["纠正数值", "描述增长曲线"])
    assert t.claim is c and t.discriminators and t.question
