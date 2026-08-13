from adverhire.probe import trap_tactics, validate_traps, is_claimable
from adverhire.models import Claim


CLAIMS = [
    Claim("优化缓存 QPS+50%", ["redis"], 50.0, "resume"),          # metric → A1
    Claim("自研压测工具", ["python"], None, "resume"),              # tech → A2
    Claim("主导推荐系统技术选型", ["kafka", "docker"], None, "resume"),  # 选型 → A3
    Claim("对外沟通多", [], None, "resume"),                        # 不可验证
]


def test_is_claimable():
    assert is_claimable(CLAIMS[0]) and is_claimable(CLAIMS[1]) and is_claimable(CLAIMS[2])
    assert not is_claimable(CLAIMS[3])


def test_trap_tactics_covers_claimable_claims_only():
    tactics = trap_tactics(CLAIMS)
    kinds = [t.kind for t in tactics]
    assert "a1_numeric" in kinds            # CLAIMS[0] 有 metric
    assert "a2_technical" in kinds          # CLAIMS[1] 有 tech
    assert "a3_decision" in kinds           # CLAIMS[2] 含"选型"
    # 不可验证的 CLAIMS[3] 无战术
    assert all(t.claim.bullet != "对外沟通多" for t in tactics)


def test_validate_traps_keeps_valid_and_binds_to_claim():
    qs = validate_traps(CLAIMS, [
        {"claim_idx": 0, "wrong_preset": "改成1800", "question": "从200怎么调到1800？", "discriminators": ["纠正"]},
    ])
    assert len(qs.questions) == 1
    assert qs.questions[0].claim is CLAIMS[0]
    assert qs.questions[0].question == "从200怎么调到1800？"


def test_validate_traps_discards_out_of_range_and_empty():
    qs = validate_traps(CLAIMS, [
        {"claim_idx": 0, "wrong_preset": "p", "question": "ok", "discriminators": []},
        {"claim_idx": 99, "wrong_preset": "p", "question": "越界", "discriminators": []},
        {"claim_idx": 3, "wrong_preset": "p", "question": "不可验证claim", "discriminators": []},  # 非 claimable
        {"claim_idx": 0, "wrong_preset": "p", "question": "   ", "discriminators": []},           # 空题
    ])
    assert len(qs.questions) == 1 and qs.questions[0].question == "ok"
