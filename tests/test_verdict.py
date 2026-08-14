from adverhire.verdict import grade_risk
from adverhire.models import SignalEvidence, Claim, Contradiction, RiskLevel


def sig(label: str, conf: float = 0.8, quote: str = "原文"):
    return SignalEvidence(label=label, quote=quote, confidence=conf)


def contra():
    return Contradiction(Claim("a", source="answer"), Claim("b", source="resume"), "scale_mismatch")


def test_grade_low_when_few_weak_signals():
    rep = grade_risk([sig("no_embodied_detail", 0.3)], [])
    assert rep.overall == RiskLevel.LOW


def test_grade_medium_with_strong_structural_signal():
    # 单个满分权重**结构性**信号(detail_exhaustion)的强信号 → MEDIUM
    rep = grade_risk([sig("detail_exhaustion", 0.8)], [])
    assert rep.overall == RiskLevel.MEDIUM


def test_grade_low_with_only_downweighted_absence_signal():
    # 缺失式五维已降权（可被 AI 注入真人口吻/假数字模仿）：单个即使 0.8 也到不了 MEDIUM
    rep = grade_risk([sig("template_cliche", 0.8)], [])
    assert rep.overall == RiskLevel.LOW
    rep2 = grade_risk([sig("no_embodied_detail", 0.8)], [])
    assert rep2.overall == RiskLevel.LOW


def test_grade_high_with_many_signals_and_contra():
    rep = grade_risk(
        [sig("detail_exhaustion", 0.8), sig("behavioral_uniformity", 0.7)],
        [contra()],
    )
    assert rep.overall == RiskLevel.HIGH


def test_by_dimension_all_five_present_and_float():
    rep = grade_risk([sig("no_embodied_detail", 0.8)], [])
    dims = rep.by_dimension
    assert set(dims) == {"template_cliche", "no_embodied_detail", "over_generalization",
                         "missing_affect", "over_standardized"}
    assert all(isinstance(v, float) for v in dims.values())


def test_invariant2_never_emits_elimination_conclusion():
    # overall 只可能取三值之一，绝不产生淘汰/录用
    for sigs, contras in (([sig("no_embodied_detail", 0.9)], [contra()]),
                          ([], []),
                          ([sig("x", 0.5), sig("y", 0.5), sig("z", 0.5), sig("w", 0.5)], [])):
        rep = grade_risk(sigs, contras, summary="供参考")
        assert rep.overall in {RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH}
        text = (rep.summary + str(rep.overall)).lower()
        assert "淘汰" not in text and "录用" not in text
