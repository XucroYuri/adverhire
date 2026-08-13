from adverhire.machine import AdversarialStateMachine
from adverhire.models import Claim, RiskLevel


def test_parse_and_tactics():
    sm = AdversarialStateMachine()
    claims, tactics = sm.parse_and_tactics([
        {"bullet": "优化缓存QPS+50%", "tech": ["redis"], "metric": 50, "source": "resume"},
    ])
    assert len(claims) == 1 and claims[0].metric == 50.0
    assert [t.kind for t in tactics] == ["a1_numeric", "a2_technical"]


def test_validate_invariant1():
    sm = AdversarialStateMachine()
    claims, _ = sm.parse_and_tactics([
        {"bullet": "优化缓存", "tech": ["redis"], "metric": 50},   # claimable
        {"bullet": "软技能", "tech": [], "metric": None},            # 不可验证
    ])
    qs = sm.validate(claims, [
        {"claim_idx": 0, "question": "怎么调的？", "wrong_preset": "p", "discriminators": []},
        {"claim_idx": 1, "question": "越界的不可验证", "wrong_preset": "p", "discriminators": []},
    ])
    assert len(qs.questions) == 1 and qs.questions[0].claim.bullet == "优化缓存"


def test_advance_full_pipeline_pure_rules():
    sm = AdversarialStateMachine()
    claims, _ = sm.parse_and_tactics([
        {"bullet": "优化缓存 QPS提升50%", "tech": ["redis"], "metric": 50},
    ])
    embodied = [Claim("其实当时我们用了lua批量回源，回滚过一次才稳定", source="answer")]
    vague = [Claim("通过深度优化和先进算法显著提升性能，达到业界领先", source="answer")]

    rep_real = sm.advance(embodied, claims, summary="见真实细节")
    rep_faked = sm.advance(vague, claims, summary="疑似AI注水")

    rank = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}
    assert rank[rep_real.overall] < rank[rep_faked.overall]   # 纯规则应能区分
    assert rep_real.overall in {RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH}


def test_machine_has_no_llm_attribute():
    sm = AdversarialStateMachine()
    assert not hasattr(sm, "_llm")  # 无 LLM 依赖
